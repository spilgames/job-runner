clean-pyc:
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

documentation:
	cd docs && make clean html

pep8:
	pep8 --show-pep8 --exclude "migrations,base.py" job_runner && echo "All good!"

unittest: clean-pyc
	DJANGO_SETTINGS_MODULE=job_runner.settings.env.testing python manage.py test

test: documentation pep8 unittest
