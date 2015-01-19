#!/usr/bin/env python
"""
sentry-auth-onelogin
====================

:copyright: (c) 2014 GetSentry LLC
:license:
"""
from setuptools import setup, find_packages


tests_require = [
    'pytest',
    'mock',
]

install_requires = [
    'sentry>=7.2.0',
]

setup(
    name='sentry-auth-onelogin',
    version='0.1.0',
    author='David Cramer',
    author_email='dcramer@gmail.com',
    url='https://www.getsentry.com',
    description='OneLogin authentication provider for Sentry',
    long_description=__doc__,
    license='',
    packages=find_packages(exclude=['tests']),
    zip_safe=False,
    install_requires=install_requires,
    tests_require=tests_require,
    extras_require={'tests': tests_require},
    include_package_data=True,
    entry_points={
        'sentry.plugins': [
            'auth_onelogin = sentry_auth_onelogin.plugin:OneLoginAuthPlugin',
         ],
    },
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Operating System :: OS Independent',
        'Topic :: Software Development'
    ],
)
