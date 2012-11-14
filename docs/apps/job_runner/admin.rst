Admin interface
===============

The admin interface behaves like any normal Django admin interface. There is
only one important modification which applies to the administration of jobs.

Normally all records would be visible when an user has access to a certain part.
The job administration is customized so that it only shows the jobs when the
user is in one of the groups listed in the job-template auth groups of that job.

To make this work properly, the user should have access to:

* all job permissions
* all reschedule exclude permissions
* all run permissions
