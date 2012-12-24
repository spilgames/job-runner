Getting started
===============

This page describes how to setup a working **Job-Runner** environment,
including the **Job-Runner WebSocket Server** and the **Job-Runner Worker**.
After a successful installation, you'll have four processes running:

#. ``./manage.py runserver``, webserver for admin, REST api and dashboard
   (part of **Job-Runner**)
#. ``./manage.py broadcast_queue``, queue broadcaster (part of **Job-Runner**)
#. ``./scripts/job_runner_ws_server``, WebSocket server (part of **Job-Runner
   WebSocket Server**)
#. ``./scripts/job_runner_worker --config-path job_runner_worker.ini``, the
   worker executing our jobs


Install all components
----------------------

#. Create three virtualenv environments called ``job-runner``,
   ``job-runner-ws-server`` and ``job-runner-worker``. If you are on Ubuntu,
   you might want to install the ``virtualenvwrapper`` package first::

       # if you need to install virtualenvwrapper first
       $ sudo apt-get install virtualenvwrapper

       $ mkvirtualenv job-runner && deactivate
       $ mkvirtualenv job-runner-ws-server && deactivate
       $ mkvirtualenv job-runner-worker && deactivate

   .. seealso:: http://virtualenvwrapper.readthedocs.org/en/latest/


#. Install the **Job-Runner** in the ``job-runner`` virtualenv. To activate
   this virtualenv, execute ``workon job-runner-worker``. See :doc:`setup` for
   installation details.

#. Install the **Job-Runner WebSocket Server** in the ``job-runner-ws-server``
   virtualenv. See the documentation in the ``job-runner-ws-server``
   repository for installation instructions.

#. Install the **Job-Runner Worker** in the ``job-runner-worker`` virtualenv.
   See the documentation in the ``job-runner-worker`` repository for
   installation instructions.


Get all components up and running
---------------------------------

Job-Runner
~~~~~~~~~~

#. Open two console tabs and execute in the first one::

       $ workon job-runner
       $ manage.py runserver

   Execute in the second tab::

       $ workon job-runner
       $ manage.py broadcast_queue

#. Open a browser and point it to ``http://localhost:8000/admin/``. This will
   open the admin interface of the **Job-Runner**. While executing
   ``manage.py syncdb`` you were asked to create superuser credentials, use
   these to login. If you did not create any, open a new console and execute::

       $ workon job-runner
       $ manage.py createsuperuser

#. In the admin interface, assign yourself to a group:

   #. Go to *Auth - Users*
   #. Click your username
   #. Under *Permissions - Groups* click the **+** icon to add yourself to a
      new group (call it *Test Group* for now)
   #. Save the user

#. Create a project:
   
   #. Go to *Job-Runner - Projects*
   #. Click the **Add project** button

      * Title: Test Project
      * Groups: select *Test Group*

   #. Click the save button

#. Create a worker for this project:

   #. Go to *Job Runner - Workers*
   #. Click on the **Add Worker** button

      * Title: Test Worker
      * Api key: testworker
      * Secret: verysecret
      * Project: Select *Test Project*

   #. Click the save button

#. You now have created a group, project and worker :) Leave both processes you
   started in the first step running!


Job-Runner WebSocket Server
~~~~~~~~~~~~~~~~~~~~~~~~~~~

#. Open a new console tab and execute::

       $ workon job-runner-ws-server
       $ job_runner_ws_server

#. That's it! Leave this process running :)


Job-Runner Worker
~~~~~~~~~~~~~~~~~

#. Open a new console tab and execute::

       $ workon job-runner-worker

#. Create a file named ``job-runner-worker.ini`` with the following content::

       [job_runner_worker]
       api_base_url=http://localhost:8000/
       api_key=testworker
       secret=verysecret 
       concurrent_jobs=4 
       log_level=debug 
       script_temp_path=/tmp 
       ws_server_hostname=localhost
       ws_server_port=5555 
       broadcaster_server_hostname=localhost
       broadcaster_server_port=5556

   Please refer to the documentation in the ``job-runner-worker`` repository
   for the meaning of these variables.

#. Now start the worker by executing::

       $ job_runner_worker --config-path job-runner-worker.ini


Congratulations! You now have all components up and running. If you point your
browser to http://localhost:8000/, you will see an empty dashboard, with
top-right a label **live**, meaning that the dashboard is connected to the
WebSocket server. If this is red with a warning, please make sure the
``job_runner_ws_server`` process is still running!
