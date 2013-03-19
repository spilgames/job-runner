Admin interface
===============

The admin interface behaves like any normal Django admin interface. There is
only one important modification which applies to the administration of jobs.

Normally all records would be visible when an user has access to a certain part
of the admin. The job administration is customized (by including the
:class:`~.PermissionAdminMixin`) so that it only shows the job-templates and
jobs the user has access to. The same applies to the project and job-template
and parent dropdown boxes when editing a job(-template).

The user has access to a job-template and job when one of the groups he is
assigned to, is in the project *auth groups* the job(-template) belongs to.

.. warning:: This only applies to the admin of job-templates and jobs!
   Super-user status will overrule this logic!

.. seealso:: :doc:`/permission_management`


``PermissionAdminMixin``
------------------------

.. autoclass:: job_runner.apps.job_runner.admin.PermissionAdminMixin
    :members:
