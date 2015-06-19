#!/usr/bin/python

import setuptools


setup_params = dict(
    name='spa',
    # Don't change this manually.  Use the 'bumpversion' tool.
    version='0.0.7',
    author='Brent Tubbs',
    author_email='brent.tubbs@gmail.com',
    packages=setuptools.find_packages(),
    include_package_data=True,

    install_requires=[
        'gunicorn>=19.1.1',
        'gwebsocket>=0.9.7',
        'Werkzeug>=0.10.1',
    ],

    tests_require=[
        'pytest',
        'websocket-client',
    ],
    description=('A Python micro framework for REST APIs and single-page-applications.'),
)

if __name__ == '__main__':
    setuptools.setup(**setup_params)
