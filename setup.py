#!/usr/bin/python

import setuptools

setup_params = dict(
    name='spa',
    version='0.0.2',
    author='Brent Tubbs',
    author_email='brent.tubbs@gmail.com',
    packages=setuptools.find_packages(),
    include_package_data=True,

    install_requires=[
        'gunicorn>=19.1.1',
        'gwebsocket>=0.9.6',
        'Werkzeug>=0.10.1',
    ],
    description=('A Python micro framework for REST APIs and single-page-applications.'),
)

if __name__ == '__main__':
    setuptools.setup(**setup_params)
