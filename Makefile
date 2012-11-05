clean-pyc:
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

documentation:
	cd docs && DJANGO_SETTINGS_MODULE=job_runner.settings.env.development make clean html
