#!/usr/bin/python

import setuptools

setup_params = dict(
    name='spa',
    version='0.0.1',
    author='Brent Tubbs',
    author_email='brent.tubbs@gmail.com',
    packages=setuptools.find_packages(),
    include_package_data=True,

    # Dependency versions are intentionally pinned to prevent surprises at
    # deploy time.  The world is not yet safely semver.
    install_requires=[
        'gwebsocket==0.9.6',
        'Werkzeug==0.10.1',
    ],
    description=('A Python micro framework for REST APIs and single-page-applications.'),
)

if __name__ == '__main__':
    setuptools.setup(**setup_params)
