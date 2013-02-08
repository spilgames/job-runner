from setuptools import find_packages, setup

import job_runner


setup(
    name='job-runner',
    version=job_runner.__version__,
    url='http://github.com/spilgames/jobrunner',
    author='Orne Brocaar',
    author_email='datawarehouse@spilgames.com',
    description='Tool for scheduling jobs and realtime monitoring',
    long_description=open('README.rst').read(),
    packages=find_packages(),
    include_package_data=True,
    scripts=['manage.py'],
    install_requires=[
        'django==1.4.2',
        'django-grappelli',
        'south',
        'MySQL-python',
        'pytz',
        'pyzmq',
        'django-tastypie==0.9.12-alpha',
        'mimeparse==0.1.3',
        'python-dateutil==1.5',
    ],
    dependency_links=[
        (
            'https://github.com/toastdriven/django-tastypie/archive/'
            '27d17b7db7afd6c81da24f64f5b4562b59134582.tar.gz'
            '#egg=django-tastypie-0.9.12-alpha'
        ),
    ]
)
