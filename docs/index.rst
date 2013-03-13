Welcome to Job-Runner's documentation!
======================================

.. toctree::
   :maxdepth: 2

   setup
   getting_started
   settings
   permission_management


Overview
--------

**Job-Runner** is a crontab like tool, with a nice web-frontend for
administration and (live) monitoring the current status. It is possible to
schedule recurring jobs, chaining jobs and the option to run or kill jobs
ad-hoc (from the dashboard). As well it provides permission management
(eg: so that some people are able to only see jobs on the dashboard, where
other people are also able to start them ad-hoc or kill them).

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


Internals
---------

.. toctree::
    :maxdepth: 2

    apps/index
