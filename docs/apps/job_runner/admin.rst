Admin interface
===============

The admin interface behaves like any normal Django admin interface. There is
only one important modification which applies to the administration of jobs.

Normally all records would be visible when an user has access to a certain part
of the admin. The job administration is customized (by including the
:class:`~.PermissionAdminMixin`) so that it only shows the jobs the user has
access to. The same applies to the job-template and parent dropdown boxes
when editing a job.

The user has access to a job when one of the groups he is assigned to, is in
the job-template *auth groups* of the job.

.. warning:: This only applies to the admin of jobs! Super-user status will
  overrule this logic!

.. seealso:: :doc:`/permission_management`


``PermissionAdminMixin``
------------------------

.. autoclass:: job_runner.apps.job_runner.admin.PermissionAdminMixin
    :members:
