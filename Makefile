clean-pyc:
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

documentation:
	cd docs && DJANGO_SETTINGS_MODULE=job_runner.settings.env.testing make clean html


unittest: clean-pyc
	DJANGO_SETTINGS_MODULE=job_runner.settings.env.testing python manage.py test

test: documentation unittest
