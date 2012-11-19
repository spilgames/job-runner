Job-Runner
==========

This project contains the Job-Runner dashboard and admin interface to
manage and view the current status of scheduled jobs.

For the full documentation see ``docs/``.


Changes
-------

v0.7.1
~~~~~~

* Check that runs received from the WebSocket server are within the current
  active project.
* Add WebKit browser notifications.


v0.7.0
~~~~~~

* **Major refactor:** It is now possible to use Sheldon assigned groups when
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
* Make it possible to override production settings by creating
  ``/bigdisk/docs/DATA/job_runner/settings_production.py``.


v0.6.0
~~~~~~

* Move Job-Runner code out of engportal project.
* Add overview of jobs + scheduling.
