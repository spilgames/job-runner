import hashlib
import hmac
# import json
import re

from tastypie.authentication import Authentication
# from tastypie.authorization import Authorization

from job_runner.apps.job_runner.models import Worker


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
        return False

    try:
        worker = Worker.objects.get(api_key=api_key_match.group(1))
    except Worker.DoesNotExist:
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

    return False


class HmacAuthentication(Authentication):
    """
    Authenticate based on request HMAC.
    """
    def is_authenticated(self, request, **kwargs):
        return validate_hmac(request)


# class JobAuthorization(Authorization):
#     """
#     Authorization for jobs.
#     """
#     def apply_limits(self, request, object_list):
#         """
#         In case of API request, limit results or show all on GET request.
#         """
#         # Limit results on API key
#         if request and 'HTTP_AUTHORIZATION' in request.META:
#             auth_header = request.META.get('HTTP_AUTHORIZATION', '')
#             api_key_match = re.match(r'^ApiKey (.*?):(.*?)$', auth_header)
#             return object_list.filter(
#                 server__public_key=api_key_match.group(1))

#         # Django session, don't limit on GET
#         elif request and request.method == 'GET':
#             return object_list

#         # Django session and request other than GET, limit on session groups
#         elif request and request.user.is_authenticated():
#             return object_list.filter(
#                 one_of_groups__in=request.user.groups.all())

#         return object_list.none()


# class RunAuthorization(Authorization):
#     """
#     Authorization for job runs.
#     """
#     def apply_limits(self, request, object_list):
#         """
#         In case of API request, limit results or show all on GET request.
#         """
#         # Limit results on API key
#         if request and 'HTTP_AUTHORIZATION' in request.META:
#             auth_header = request.META.get('HTTP_AUTHORIZATION', '')
#             api_key_match = re.match(r'^ApiKey (.*?):(.*?)$', auth_header)
#             return object_list.filter(
#                 job__server__public_key=api_key_match.group(1))

#         # Django session, don't limit on GET
#         elif request and request.method == 'GET':
#             return object_list

#         # Django session and request other than GET, limit on session groups
#         elif request and request.user.is_authenticated():
#             return object_list.filter(
#                 job__one_of_groups__in=request.user.groups.all())

#         return object_list.none()
