Permission management
=====================

Likely, after setting up a few jobs, you would like to give people within your
team access to see the current job overview etc... For this, there are three
levels of permissions:

* View status of jobs including log-output
* Permission to schedule a job *now* or to suspend a job
* Access to admin interface to add / edit / remove jobs


View status of jobs including log-output
----------------------------------------

To make jobs visible to a user, make sure the user is within at least one group
that is linked to the project the job belongs to.


Permission to schedule a job *now* or to suspend a job
------------------------------------------------------

To grant the user permission to schedule a job *now* or to suspend a job, make
sure the user is within at least one auth-group that is linked to the project
the job belongs to.


Access to admin interface to add / edit / remove jobs
-----------------------------------------------------

When the above is already true, you can grant a user admin permission by
ticking the *Staff status* box in the admin interface for this user. Make
sure the user (or one of the groups the user belogs to) has at least the
following permissions:

* All *admin | log entry | ...*
* All *job_runner | job | ...*
* All *job_runner | job template | ...*
* All *job_runner | reschedule exclude | ...*
* All *job_runner | run | ...*
* All *sessions | ...*

Of course, you can finegrain this to your own needs (eg when you don't want
your users to create or delete job-templates).


.. seealso:: :doc:`apps/job_runner/admin` for more technical details
