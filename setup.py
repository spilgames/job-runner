from setuptools import find_packages, setup

import job_runner


setup(
    name='job-runner',
    version=job_runner.__version__,
    url='http://github.com/spilgames/job-runner',
    license='BSD',
    author='Spil Games',
    author_email='datawarehouse@spilgames.com',
    description='Tool for scheduling jobs and realtime monitoring',
    long_description=open('README.rst').read(),
    packages=find_packages(),
    include_package_data=True,
    scripts=['manage.py'],
    install_requires=[
        'django==1.4.2',
        'django-grappelli',
        'django_compressor',
        'django-smart-selects',
        'django-tastypie==0.9.14',
        'south',
        'pytz',
        'pyzmq',
        'mimeparse==0.1.3',
        'python-dateutil==1.5',
    ],
)
