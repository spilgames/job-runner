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


Projects
~~~~~~~~

``GET /api/v1/project/``
    Returns a list of available projects.

``GET /api/v1/project/{PROJECT_ID}/``
    Returns the details of a specific project-id.


Workers
~~~~~~~

``GET /api/v1/worker/``
    Returns a list of available workers.

``GET /api/v1/worker/{WORKER_ID}/``
    Returns the details of a specific worker-id.


Job-templates
~~~~~~~~~~~~~

``GET /api/v1/job_template/``
    Returns a list of available job-templates.

``GET /api/v1/job_template/{JOB_TEMPLATE_ID}/``
    Returns the details of a specific job-template id.


Jobs
~~~~

``GET /api/v1/job/``
    Returns a list of available jobs.

``GET /api/v1/job/{JOB_ID}/``
    Returns the details of a specific job-id.


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

``GET /api/v1/run/{RUN_ID}/``
    Returns the details of a specific job run.

``PATCH /api/v1/run/{RUN_ID}/``
    When the ``return_dts`` is patched, the job will be automatically
    rescheduled (if needed).
