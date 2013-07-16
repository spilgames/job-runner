REST interface
==============

The Job runner has a REST interface so that the workers can fetch and modify
data. There are two types of authentication:

* Django session (for status dashboard)
* HMAC authentication (for worker daemons)


Django session
~~~~~~~~~~~~~~

When the request contains a logged in user (the user has a session and is
logged in) it will automatically get access, limited to ``GET`` requests.


HMAC authentication
~~~~~~~~~~~~~~~~~~~

When request contains a valid ``Authentication`` header, containing a
public-key and api key, it will get access to the full set of available
methods.

The used HMAC is HMAC-SHA1, with a message in the following format::

    Uppercased request method + full request path (path + query string, if
    applicable) + path + query string, if applicable.

The format of the header is::

    Authentication: ApiKey api_key:hmac_sha1


Available end-points
--------------------

.. note:: You can append ``schema/`` to the end of the URL to get information
    about the schema!

Groups
~~~~~~

``GET /api/v1/group/``
    Returns a list of available (and thus assigned) groups.

``GET /api/v1/group/{GROUP_ID}/``
    Returns the details of a specific job-id.


Projects
~~~~~~~~

``GET /api/v1/project/``
    Returns a list of available projects.

``GET /api/v1/project/{PROJECT_ID}/``
    Returns the details of a specific project-id.


Worker-pools
~~~~~~~~~~~~

``GET /api/v1/worker_pool/``
    Returns a list of available worker-pools. The following filters are
    allowed:

    title
        The exact title of the worker-pool.


``GET /api/vi/worker-pools/{WORKER_POOL_ID}/``
    Return the details of a specific worker-pool id.


Workers
~~~~~~~

``GET /api/v1/worker/``
    Returns a list of available workers.

``GET /api/v1/worker/{WORKER_ID}/``
    Returns the details of a specific worker-id.

``PATCH /api/v1/worker/{WORKER_ID}/``
    Update one or more worker fields (used to update
    the ``ping_response_dts``).


Job-templates
~~~~~~~~~~~~~

``GET /api/v1/job_template/``
    Returns a list of available job-templates. The following filters are
    allowed:

    title
        The exact title of the job-template.


``GET /api/v1/job_template/{JOB_TEMPLATE_ID}/``
    Returns the details of a specific job-template id.


Jobs
~~~~

``GET /api/v1/job/``
    Returns a list of available jobs. The following filters are allowed:

    job_template
        The the job-template of the job.

    title
        The exact title of the job.


``GET /api/v1/job/{JOB_ID}/``
    Returns the details of a specific job-id.

``PUT /api/v1/job/{JOB_ID}/``
    Update the job (used by AngularJS to enable / disable enqueue of a job).


Runs
~~~~

``GET /api/v1/run/``
    Returs a list of runs. You can filter the state by adding ``state`` as a
    keyword argument. Possible values are:

    * ``scheduled`` (scheduled by not picked up yet by a worker)
    * ``in_queue`` (picked up by a worker, but not yet started)
    * ``started`` (started, but not completed yet)
    * ``completed`` (completed, either with or without error)
    * ``completed_successful`` (completed without error)
    * ``completed_with_errors`` (completed with error)
    * ``last_completed`` (last completed runs for each job)

``GET /api/v1/run/{RUN_ID}/``
    Returns the details of a specific job run.

``POST /api/v1/run/``
    Create a new run (used for ad-hoc scheduling a job in the dashboard).

``PATCH /api/v1/run/{RUN_ID}/``
    When the ``return_dts`` is patched, the job will be automatically
    rescheduled (if needed).


Kill-requests
~~~~~~~~~~~~~

``GET /api/v1/kill_request/``
    Returns a list of kill-requests.

``GET /api/v1/kill_request/{KILL_REQUEST_ID}/``
    Returns the details of a specific kill-request id.

``POST /api/v1/kill_request/``
    Create a new kill-request.

``PATCH /api/v1/kill_request/{KILL_REQUEST_ID}/``
    Update one or more fields of the given kill-request id.


Run-logs
~~~~~~~~

``GET /api/v1/run_log/``
    Returns a list of run-logs.

``GET /api/vi/run_log/{RUN_LOG_ID}/``
    Returns the details of a specific run-log id.

``POST /api/v1/run_log/``
    Create a new run-log.

``PATCH /api/v1/run_log/{RUN_LOG_ID}/``
    Update one or more fields of the given run-log id.
