Job-Runner
==========

.. image:: https://api.travis-ci.org/spilgames/job-runner.png?branch=master
    :alt: Build Status
    :target: https://travis-ci.org/spilgames/job-runner

**Job-Runner** is a crontab like tool, with a nice web-frontend for
administration and (live) monitoring the current status.

Features:

* Schedule recurring jobs
* Chaining of jobs
* Load-balance workers by putting them in a pool
* Schedule jobs to run on all workers within a pool
* Live dashboard (with option to kill runs and ad-hoc scheduling)
* Multiple projects and per-project permission management


The whole project consists of three separate components (and repositories):

* **Job-Runner**: provides the REST interface, admin interface and (live)
  dashboard. As well this component provides a long-running process
  (``manage.py broadcast_queue``) to broadcast messages (over ZeroMQ) to the
  workers. See: https://github.com/spilgames/job-runner

* **Job-Runner Worker**: the process that is responsible for executing the job.
  It subscribes to (ZeroMQ) messages coming from ``broadcast_queue``, send data
  back over the REST interface and publishes events to the
  *Job-Runner WebSocket Server*.
  You can run as many workers as you like, as long as every worker has it's own
  API key (eg: when you want to run jobs on multiple servers or under different
  usernames on the same server). API keys can be created in the *Job-Runner*
  admin interface.
  See: https://github.com/spilgames/job-runner-worker

* **Job-Runner WebSocket Server**: will subscribe to *Job-Runner Worker* events
  and re-broadcast them to WebSocket connections coming from the *Job-Runner*
  dashboard. This makes it possible to add realtime monitoring to the
  dashboard.
  See: https://github.com/spilgames/job-runner-ws-server


Links
-----

* `documentation <https://job-runner.readthedocs.org/>`_
* `job-runner source <https://github.com/spilgames/job-runner>`_
* `job-runner-worker source <https://github.com/spilgames/job-runner-worker>`_
* `job-runner-ws-server source <https://github.com/spilgames/job-runner-ws-server>`_


Changes
-------

v3.5.2
~~~~~~

* Added more logging (notifications) and fixed minor logging issues

v3.5.1
~~~~~~

* Add logging about scheduling, job kills and general failures

v3.5.0
~~~~~~

* Add support for filtering on ``title`` in the API.
* Add support for updating and creating jobs in the API.


v3.4.0
~~~~~~

* Add ``worker_version`` and ``concurrent_jobs`` fields to the Worker resource.
  These fields will be send by the worker at every ping response and are
  displayed in the admin.


v3.3.0
~~~~~~

* Handle error response when the user does not have access anymore to the
  worker data in the REST API. This can happen when a worker is removed from a
  worker-pool.
* Show the full job-chain on the jobs page.
* Add check to assure that there is no recursion in the job-chain
  (parent/child relations).


v3.2.0
~~~~~~

* Make it possible to continue the chain of jobs when one of the jobs failed
  (or when a worker failed when run on all workers is selected).
* Add management-command ``health_check`` which marks runs assigned to
  unresponsive workers as failed and alert when all workers within a pool
  are unresponsive.
* Fix ``order_by`` in ``reschedule`` method.


v3.1.3
~~~~~~

* Redirect to the last selected project (failing that, to the first project
  in the list).


v3.1.2
~~~~~~

* Fix: do not schedule disabled children (regression introduced by the new
  way of scheduling in v3.1.0).


v3.1.1
~~~~~~

* Markdown support for job descriptions was added.
* Scheduled runs are now displayed in the job details.
* Improve performance by increasing the default API page-size to 200.
* Show the user a warning when there are no projects.


v3.1.0
~~~~~~

.. warning:: Before deploying this version, make sure that there aren't any
             running jobs! One way to do this is to disable all projects in the
             admin, let all runs complete, and then upgrade.

* Schedule the next run before broadcasting the current scheduled run.
* Remove "after complete dts" reschedule option.


v3.0.3
~~~~~~

* Make sure to rollback transaction in case of an exception in
  ``broadcast_queue`` management command.
* Fix issue with "run on all workers" jobs, where it wasn't detected that
  all siblings finished.


v3.0.2
~~~~~~

* Apply "Save as new" button to all model admins.
* Fix validation of the reschedule interval field (should not accept 0).
* Add dropdown option to see the runs / jobs of all projects.
* Show assigned workers in last 100 completed runs.
* The ``broadcast_queue`` command is now locking the selected runs. This is
  needed to make sure that when there are multiple broadcasters, no duplicated
  runs are generated (in case of run on all workers).


v3.0.1
~~~~~~

* Fix re-schedule issue (duplicates) when manually schedule a recurring job.
* Fix schedule-time when switching from or to daylight saving-time. Before
  the time of a job would change when switching from or to DST. Now a job
  will be always re-scheduled at the same time (when increment schedule dts by
  interval is selected).


v3.0.0
~~~~~~

* New dashboard layout to make it more easy to view large sets of data.
* Optimization of the initial load of data (fewer API requests).
* Add support to run a job across all workers within a worker-pool.


v2.0.1
~~~~~~

* Optimize the way how the ``ModelAuthorization`` class is testing if the user
  or worker has access to the object.


v2.0.0
~~~~~~

* Restructure the relations between models. Workers are now project independent
  and are grouped by pools. Permissions are now managed on project level
  (instead on project and job-template level) By assigning a job to a pool
  containing multiple workers, the job will be loadbalanced
  (by selecting a random worker).

  After upgrading, make sure to run ``manage.py migrate`` to migrate your
  data to the new structure.

  .. warning:: Before running ``manage.py migrate``, make a backup of your
               data! The new structure is not backwards compatible and
               thus can not be migrated backwards.


v1.4.3
~~~~~~

* Fix duplicated enqueues when the worker is down or the enqueue is disabled
  for the job. This happened for example when a parent-job tried to schedule
  a child job which was disabled.


v1.4.2
~~~~~~

* Fix the issue where runs from other projects than the selected one, were
  rendered on the dashboard.


v1.4.1
~~~~~~

* Add caching of objects to improve the performance (frontend).


v1.4.0
~~~~~~

* Complete refactor of front-end code. The front-end is now based on AngularJS.
* Misc admin interface improvements (sorting, labels, etc...).
* Add if the run was manual and / or killed to the error e-mail template.
* Add compressor for JavaScript code.


v1.3.3
~~~~~~

* Broadcast ping requests to the worker (default: every 5 minutes) and show
  last ping response in admin. This will make it more easy to discover problems
  with workers.


v1.3.2
~~~~~~

* Spil specific settings removed.


v1.3.1
~~~~~~

* Fix run status modal JavaScript code (was not working when there is no log
  yet).
* Fix related name of ``run_log``, to make sure it shows up correctly in the
  template when there is an error.


v1.3.0
~~~~~~

* Move logs to separate model and RESTful resource. Make sure that you update
  the worker to >= v1.1.0.


v1.2.10
~~~~~~~

* Show full path (project - template - worker ...) in object title.
* Improve ordering of objects in the admin.
* Added getting started section to the docs.
* Misc documentation improvements.


v1.2.9
~~~~~~

* Fix kill button so that it is only visible when the user has permission to
  kill a job-run (would else result in a HTTP error).


v1.2.8
~~~~~~

* Add option in dashboard to kill job-runs.
* Fix time-zone in failed-run e-mail template (will now use the time-zone
  configured in the Django config).


v1.2.7
~~~~~~

* Disable the job when it failed more than x times (optional setting).


v1.2.6
~~~~~~

* Make it possible to disable the enqueue of a project, worker or job-template.


v1.2.5
~~~~~~

* Display parent - child relationships in job details.
* Fix an other issue with the run broadcaster to make sure it doesn't broadcast
  multiple runs for the same job.
* Fix styling glitches by adding a ``boot.css`` which is used as long the
  ``.less`` files aren't compiled yet.


v1.2.4
~~~~~~

* Fix run broadcaster so that it doesn't send runs to the workers when there
  is still an other run for the same job active (in queue or started).
* Fix autoselect environment settings.
* Update hostnames in configuration.


v1.2.3
~~~~~~

* Add filters to limit the number of displayed jobs.
* Add status icon to display if there is a connection with the WebSocket server
* Add option for monthly re-scheduling **Note:** monthly re-scheduling works
  by incrementing the ``dts`` with the number of days that are in the ``dts``.
  When incrementing by multiple months, it will check the days for each month.


v1.2.2
~~~~~~

* Add description fields to projects, workers, job-templates and jobs
* Add ``TransactionMiddleware``
* Fix rescheduling when two runs are active of the same job


v1.2.1
~~~~~~

* Add MySQL to requirements.txt (since the python setup.py install is
  creating a zipped .egg which doesn't work when the user does not have
  a homedir (or when the homedir is not executable).


v1.2.0
~~~~~~

* Show job details in a column instead of a modal
* Show last 100 runs of a job incl. duration graph
* Fix ``AUTHENTICATION_BACKENDS`` setting for staging and production
  (without ``ModelBackend`` included, permissions are not working!)
* A job-title must now be unique per job-template
* Show re-schedule interval in job details


v1.1.1
~~~~~~

* Fix dependencies in ``setup.py`` (was not using the development version
  from GitHub).


v1.1.0
~~~~~~

* Run and job details are made deeplinkable
* Runs and jobs that are suspended are greyed-out


v1.0.0
~~~~~~

* Fix size (height) of run / job headers
* Fix order of run objects
* Fix escaping of HTML characters in job script and log output
* Enable timezone, all data is now presented (and expected to be) in the
  *Europe/Amsterdam* timezone
* Order scheduled runs ascending (first to run on top)
* Add option to schedule children or not, when manually scheduling runs

v0.7.4
~~~~~~

* Internal related changes.


v0.7.3
~~~~~~

* Add ``job_runner.settings.env.production_longrun`` settings module for long
  running processes to avoid "cached" results.


v0.7.2
~~~~~~

* Fix issue where filtering the groups would result in duplicated results.
* Remove WebKit browser notifications, since it was breaking the front-end in
  Firefox.


v0.7.1
~~~~~~

* Check that runs received from the WebSocket server are within the current
  active project.
* Add WebKit browser notifications.


v0.7.0
~~~~~~

* **Major refactor:** It is now possible to use AD assigned groups when
  creating projects. Since basically all models are changed / renamed, it was
  not possible to migrate old data to the new structure. Therefore you should
  re-create the database!
* Add ``broadcast_queue`` management command to publish enqueueable runs to
  the workers.


v0.6.2
~~~~~~

* Add missing static-file and logging settings.


v0.6.1
~~~~~~

* Add MySQL package as a requirement + update requirements in docs.
* Make it possible to override production settings.


v0.6.0
~~~~~~

* Create standalone application.
* Add overview of jobs + scheduling.
