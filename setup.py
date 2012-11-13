from setuptools import find_packages, setup

import job_runner


setup(
    name='job-runner',
    version=job_runner.__version__,
    url='http://github.com/spilgames/jobrunner',
    author='Orne Brocaar',
    author_email='orne.brocaar@spilgames.com',
    description='Tool for scheduling jobs and realtime monitoring',
    long_description=open('README.rst').read(),
    packages=find_packages(),
    include_package_data=True,
    scripts=['manage.py'],
    install_requires=[
        'django==1.4.2',
        'django-grappelli',
        'south',
        'uwsgi',
        'MySQL-python',
        'django-tastypie==0.9.12-alpha',
        'mimeparse==0.1.3',
        'python-dateutil==1.5',
    ],
)
