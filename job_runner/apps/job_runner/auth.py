import hashlib
import hmac
import re
import logging

from django.db.models import Q
from tastypie.authentication import Authentication
from tastypie.authorization import Authorization

from job_runner.apps.job_runner.models import Worker

logger = logging.getLogger(__name__)


def validate_hmac(request):
    """
    Validate the HMAC of an incoming request.

    :param request:
        The incoming request object.

    :return:
        A ``bool`` indicating if the request is valid.

    This will test the ``Authentication`` header for valid keys. The following
    format is expected::

        Authorization: ApiKey api_key:hmac_sha1

    ``public_key``
        Is the public key as stored in the ApiKey model.

    ``hmac_sha1``
        The HMAC-SHA1 generated over the uppercased request method + full
        request path (path + query string, if applicable) + request body,
        if applicable.

    """
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    api_key_match = re.match(r'^ApiKey (.*?):(.*?)$', auth_header)

    if not api_key_match:
        logger.error('api key mismatch')
        return False

    try:
        worker = Worker.objects.get(api_key=api_key_match.group(1))
    except Worker.DoesNotExist:
        logger.error('worker does not exist')
        return False

    hmac_message = '{request_method}{full_path}{request_body}'.format(
        request_method=request.method,
        full_path=request.get_full_path(),
        request_body=request.raw_post_data,
    )

    expected_hmac = hmac.new(
        str(worker.secret), hmac_message, hashlib.sha1)

    if expected_hmac.hexdigest() == api_key_match.group(2):
        return True

    logger.error('hmac mismatch')

    return False


class HmacAuthentication(Authentication):
    """
    Authenticate based on request HMAC.
    """
    def is_authenticated(self, request, **kwargs):
        return validate_hmac(request)


class ModelAuthorization(Authorization):
    """
    Model authorization.

    The purpose of this custom authorization class is to limit the number of
    results returned to the user based on session or API-key.

    In case of the session it will be limited to the groups the logged-in
    user is assiged to, in case of the API-key it will be limited to the
    data that refereces back to the API-key.

    :param api_key_path:
        The path relative from the used model to the API-key. For the
        ``JobTemplate`` this would be ``'worker__api_key'``.

    :param user_groups_path:
        The path relative from the used model to the groups the user belongs
        to. For the ``JobTemplate`` this would be
        ``'worker__project__groups'``.

    :param auth_user_groups_path:
        The path relative from the used model to the groups that are authorized
        to make modifications. Default is ``None``. For the ``Job`` model this
        would be ``'job_template__auth_groups'``.

    """
    def __init__(
            self, api_key_path, user_groups_path, auth_user_groups_path=None):
        self.api_key_path = api_key_path
        self.user_groups_path = user_groups_path
        self.auth_user_groups_path = auth_user_groups_path

    def filter_object_list(self, object_list, bundle):
        """
        Return a filtered list of objects that the user has permission to.
        """
        request = bundle.request

        # request is coming from the worker, use the ``api_key_path``.
        if request and 'HTTP_AUTHORIZATION' in request.META:
            auth_header = request.META.get('HTTP_AUTHORIZATION')
            api_key_match = re.match(r'^ApiKey (.*?):(.*?)$', auth_header)
            return object_list.filter(
                **{self.api_key_path: api_key_match.group(1)}).distinct()

        # request is from a logged in user (django session)
        elif (request and request.user.is_authenticated()
              and request.user.groups.count() > 0):
            groups_or = None

            if self.user_groups_path == "":
                path = 'name'
            else:
                path = '{0}__name'.format(self.user_groups_path)

            for group in request.user.groups.all():
                q_obj = Q(**{path: group.name})
                if not groups_or:
                    groups_or = q_obj
                else:
                    groups_or = groups_or | q_obj

            object_list = object_list.filter(groups_or).distinct()

            # apply extra filters when the request is not a GET
            if (request.method != 'GET' and
                    self.auth_user_groups_path is not None):
                groups_or = None

                if self.auth_user_groups_path == "":
                    path = 'name'
                else:
                    path = '{0}__name'.format(self.auth_user_groups_path)

                for group in request.user.groups.all():
                    q_obj = Q(**{path: group.name})
                    if not groups_or:
                        groups_or = q_obj
                    else:
                        groups_or = groups_or | q_obj

                object_list = object_list.filter(groups_or).distinct()

            return object_list

        return object_list.none()

    def read_list(self, object_list, bundle):
        return self.filter_object_list(object_list, bundle)

    def read_detail(self, object_list, bundle):
        # seems like this is the way to authorize /schema/ request?
        # it looks like tastypie is creating an empty (dummy) object, which
        # is not saved
        if not bundle.obj.id:
            return True

        obj_list = self.filter_object_list(object_list, bundle)
        return bundle.obj in obj_list.filter(pk=bundle.obj.pk)

    def update_detail(self, object_list, bundle):
        obj_list = self.filter_object_list(object_list, bundle)
        return bundle.obj in obj_list.filter(pk=bundle.obj.pk)
