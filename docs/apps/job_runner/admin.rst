Admin interface
===============

The admin interface behaves like any normal Django admin interface. There is
only one important modification which applies to the administration of jobs.

Normally all records would be visible when an user has access to a certain part
of the admin. The job administration is customized so that it only shows the
jobs the user has access to.

The user has access to a job when one of the groups he is assigned to, is in
the job-template *auth groups* of the job.

To make this work properly, the user (or one of his groups) should have the
following permissions:

* All *admin | log entry | ...*
* All *job_runner | job | ...*
* All *job_runner | reschedule exclude | ...*
* All *job_runner | run | ...*
* All *sessions | ...*
