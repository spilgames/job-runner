Setup Job-Runner
================

.. note:: By default the settings in ``job_runner.settings.env.development``
   are used. These settings should work out-of-the box for local development
   (using Sqlite as a database back-end). Use the ``--settings`` argument of
   ``manage.py`` to use different settings.

#. Make sure you have all requirements installed (the exact package names
   can vary per distribution, these are for Ubuntu).:

   * ``python-dev``
   * ``virtualenvwrapper``
   * ``build-essential``
   * ``libmysqlclient-dev``

#. Create a Virtualenv (http://virtualenvwrapper.readthedocs.org/en/latest/),
   to make sure all requirements are installed in an isolated environment. This
   is not required, but it will keep your system clean :)

   ::

       $ mkvirtualenv job-runner

#. Install the Job-Runner (which will fetch all Python requirements as well)::

       $ pip install job-runner

   Alternatively, you could clone the ``job-runner`` repository and install
   the package in development mode. Any changes you make will be reflected
   immediately without having to do an install again::

       $ python setup.py develop
       $ pip install -r test-requirements.txt

#. Initialize the database and run the migations::

   $ manage.py syncdb
   $ manage.py migrate
   $ manage.py collectstatic

#. Run ``manage.py runserver``. This will start a development server with
   the default development settings.

#. Run ``manage.py broadcast_queue``. This will start the queue broadcaster.
