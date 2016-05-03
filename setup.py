#!/usr/bin/python

import os
import setuptools

# To update Spa's version.txt file and ensure that a matching tag is created in
# version control, please use the 'bumpversion' command line tool.

here = os.path.dirname(os.path.realpath(__file__))
version_file = os.path.join(here, 'spa', 'version.txt')
with open(version_file) as f:
    version = f.read().strip()

setup_params = dict(
    name='spa',
    version=version,
    author='Brent Tubbs',
    author_email='brent.tubbs@gmail.com',
    packages=setuptools.find_packages(),
    include_package_data=True,
    install_requires=[
        'gunicorn>=19.4.1',
        'gwebsocket>=0.9.7',
        'PyJWT>=1.4.0',
        'six>=1.10.0',
        'utc>=0.0.3',
        'Werkzeug>=0.10.1',
    ],
    description=('A Python micro framework for REST APIs and single-page-applications.'),
)

if __name__ == '__main__':
    setuptools.setup(**setup_params)
