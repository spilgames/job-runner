Job-Runner
==========

This project contains the Job-Runner dashboard and admin interface to
manage and view the current status of scheduled jobs.

For the full documentation see ``docs/``.


Changes
-------

v1.2.0
~~~~~~

* Show last 100 runs of a job.


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

* Deployar related changes.


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
