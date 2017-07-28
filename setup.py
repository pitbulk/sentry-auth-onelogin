#!/usr/bin/env python
"""
sentry-auth-onelogin
====================
"""
from setuptools import setup, find_packages


install_requires = [
    'python3-saml>=1.2.6'
]

tests_require = [
    'flake8>=2.0,<2.1',
]

setup(
    name='sentry-auth-onelogin',
    version='0.1.1.dev',
    author='Sentry',
    author_email='support@getsentry.com',
    url='https://www.getsentry.com',
    description='Onelogin SAML SSO provider for Sentry',
    long_description=__doc__,
    license='Apache 2.0',
    packages=find_packages(exclude=['tests']),
    zip_safe=False,
    install_requires=install_requires,
    tests_require=tests_require,
    extras_require={'tests': tests_require},
    include_package_data=True,
    entry_points={
        'sentry.apps': [
            'auth_onelogin = sentry_auth_onelogin',
        ],
    },
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Operating System :: OS Independent',
        'Topic :: Software Development'
    ],
)
