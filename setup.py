#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""
import os
import platform

SHORT_DESCRIPTION = "Python client for etcd v3 (Using gRPC-JSON-Gateway)"

try:  # for pip >= 10
    from pip._internal.req import parse_requirements
except ImportError:  # for pip <= 9.0.3
    from pip.req import parse_requirements
from setuptools import setup, find_packages

PY2 = platform.python_version_tuple()[0] == '2'

print(SHORT_DESCRIPTION)
print(os.listdir(os.curdir))

with open('README.md') as readme_file:
    readme = readme_file.read()

with open('CHANGELOG.md') as history_file:
    history = history_file.read()

# parse_requirements() returns generator of pip.req.InstallRequirement objects
# if PY2:
#     install_reqs = parse_requirements('requirements.txt', session='')
# else:
#     install_reqs = parse_requirements('requirements_py3.txt', session='')

install_reqs = parse_requirements('requirements.txt', session='')

# reqs is a list of requirement
requirements = [str(ir.req) for ir in install_reqs]

setup_requirements = [
    # 'pytest-runner',
]

if PY2:
    test_reqs = parse_requirements('requirements_dev.txt', session='')
else:
    test_reqs = parse_requirements('requirements_dev_py3.txt', session='')

test_requirements = list({str(ir.req) for ir in test_reqs} - set(requirements))

setup(
    name='etcd3-py',
    version='0.1.6',
    description=SHORT_DESCRIPTION,
    long_description=readme + '\n\n' + history,
    long_description_content_type="text/markdown",
    author="Renjie Cai",
    author_email='revol.cai@gmail.com',
    url='https://github.com/revolution1/etcd3-py',
    packages=find_packages(include=['etcd3*']),
    package_data={
        "etcd3": ["*.json"],
    },
    # entry_points={
    #     'console_scripts': [
    #         'etcd3cli=etcd3.cli:main'
    #     ]
    # },
    include_package_data=True,
    install_requires=requirements,
    license="Apache Software License 2.0",
    python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*',
    zip_safe=False,
    keywords='etcd3',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    test_suite='tests',
    tests_require=test_requirements,
    setup_requires=setup_requirements,
    extras_require={
        ':python_version >= "3.5"': [
            'aiohttp',
        ],
        ':python_version < "3.4"': [
            'enum34>=1.1.6',
        ],
    },
)
