Overview
========

The **Job-Runner** is a crontab like tool, with a nice web-frontend for
admistration and monitoring the current status. It consists of 3 separate
components (and repositories):

* **Job-Runner** (this repository): provides the REST interface,
  admin interface and (live) dashboard. As well this contains a long-running
  command (``manage.py broadcast_queue``) to broadcast commands (like enqueue,
  kill requests, ...) to the workers.

* **Job-Runner WebSocket Server**: provides a WebSocket gateway to Worker
  events. This is used for real-time communication between workers and the
  **Job-Runner** dashboard (eg: to make the dashboard status live).

* **Job-Runner Worker**: the component that executes the job. It is possible
  to have multiple workers. For example when you have multiple servers on
  which jobs should run and / or when you want to execute jobs under different
  user-accounts.


.. image:: images/overview.*
    :width: 100%
