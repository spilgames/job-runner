Job-Runner
==========

This project contains the Job-Runner dashboard and admin interface to
manage and view the current status of scheduled jobs.

For the full documentation see ``docs/``.


Changes
-------

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
