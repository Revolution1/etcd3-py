#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""
import platform

from setuptools import setup, find_packages

PY3 = platform.python_version_tuple()[0] == '3'

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    'click==6.7',
    'enum34>=1.1.6',
    'six>=1.11.0',
    'requests>=2.10.0',
]

if PY3:
    requirements.append('aiohttp')

setup_requirements = [
    # 'pytest-runner',
    # TODO(revolution1): put setup requirements (distutils extensions, etc.) here
]

test_requirements = [
    'pytest',
    'mock',
    # TODO: put package test requirements here
]

setup(
    name='etcd3-py',
    version='0.0.1',
    description="Python client for etcd v3 (Using grpc-json-gateway) Edit",
    long_description=readme + '\n\n' + history,
    author="Renjie Cai",
    author_email='revol.cai@gmail.com',
    url='https://github.com/revolution1/etcd3-py',
    packages=find_packages(include=['etcd3']),
    # entry_points={
    #     'console_scripts': [
    #         'etcd3cli=etcd3.cli:main'
    #     ]
    # },
    include_package_data=True,
    install_requires=requirements,
    license="Apache Software License 2.0",
    zip_safe=False,
    keywords='etcd3',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    test_suite='tests',
    tests_require=test_requirements,
    setup_requires=setup_requirements,
)
