Overview
========

The Job-Runner consists of 3 separate components (and repositories):

* **Job-Runner** (this repository): provides the REST interface,
  admin interface and (live) dashboard.

* **Job-Runner Worker**: runs on each server on which it should be possible
  to run a job.

* **Job-Runner WebSocket Server**: provides a WebSocket gateway to Worker
  events. This is used to make the **Job-Runner** dashboard realtime.


The life of a job (run)
-----------------------

When a job has been scheduled (and thus a run has been created), it will be
picked up by the ``broadcast_queue`` management command. This will publish
it (addressed to the right worker) to all its subscribers (workers) over
ZeroMQ.

The assigned worker will receive the scheduled run and will put it in its own
queue so one of the worker slots can execute it when it becomes available.
Each status update will be send back to the REST interface and an event
will be send to the **WebSocket Server** (over ZeroMQ) so the update can be
picked up immediately by the live dashboard.

The REST interface will re-schedule the job if needed (create a new run),
when the job has been marked as completed by the worker.
