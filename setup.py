#! /usr/bin/env python
#  coding=utf-8
"""Accelerator API setup script

run "./setup.py --help-commands" for help.
"""
from datetime import datetime
from os import chdir, environ
from os.path import dirname, abspath, join
from sys import argv

from setuptools import setup, find_packages

# Sets Package information
PACKAGE_INFO = dict(
    name='apyfal',
    description='Apyfal is a powerful and flexible '
                'toolkit to operate FPGA accelerated functions.',
    long_description_content_type='text/markdown; charset=UTF-8',
    classifiers=[
        # Must be listed on: https://pypi.org/classifiers/
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Topic :: System :: Distributed Computing',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Operating System :: OS Independent'
    ],
    keywords='cloud accelerator fpga hpc',
    author='Accelize',
    author_email='info@accelize.com',
    url='https://github.com/Accelize/apyfal',
    project_urls={
        'Documentation': 'https://apyfal.readthedocs.io',
        'Download': 'https://pypi.org/project/apyfal',
        'AccelStore': 'https://accelstore.accelize.com',
        'Accelize Website': 'https://www.accelize.com',
        'Contact': 'https://www.accelize.com/contact',
    },
    license='Apache License, Version 2.0',
    python_requires='>=2.7,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*',
    install_requires=[
        'requests>=2.9.0',
        'requests_toolbelt>=0.7.1',
        'pycosio>1.0.0',
        'cryptography>=2.1',

        # Python 2.7 compatibility
        'futures>=3.1.1; python_version == "2.7"',
        'ipaddress>=1.0.18; python_version == "2.7"',

        # Makes AWS as default since it is the only one ready
        # to production today. AWS extra is kept for compatibility.
        'boto3>=1.5.0'],

    extras_require={
        # CSP specific requirements
        'Alibaba': [
            'pycosio[oss]',
            'aliyun-python-sdk-core>=2.5.0; python_version == "2.7"',
            'aliyun-python-sdk-core-v3>=2.5.0; python_version >= "3.4"'],
        'AWS': ['boto3>=1.5.0', 'pycosio[s3]'],
        'OpenStack': [
            'python-novaclient>=8.0.0',
            'python-neutronclient>=6.0.0',
            'pycosio[swift]']},

    setup_requires=['setuptools'],
    tests_require=['pytest'],
    packages=find_packages(exclude=['docs', 'tests', 'rest_api']),
    zip_safe=True,
    command_options={},
    entry_points={'console_scripts': ['apyfal=apyfal.__main__:_run_command']})

# Add OpenStack sub extra:
PACKAGE_INFO['extras_require']['OVH'] = PACKAGE_INFO[
    'extras_require']['OpenStack']

# Gets package __version__ from package
SETUP_DIR = abspath(dirname(__file__))
with open(join(SETUP_DIR, 'apyfal', '__init__.py')) as source_file:
    for line in source_file:
        if line.rstrip().startswith('__version__'):
            PACKAGE_INFO['version'] = line.split('=', 1)[1].strip(" \"\'\n")
            break

# Gets long description from readme
with open(join(SETUP_DIR, 'README.md')) as source_file:
    PACKAGE_INFO['long_description'] = source_file.read()

# Add pytest_runner requirement if needed
if {'pytest', 'test', 'ptr'}.intersection(argv):
    PACKAGE_INFO['setup_requires'].append('pytest-runner')

# Add Sphinx requirements if needed
elif 'build_sphinx' in argv:
    PACKAGE_INFO['setup_requires'] += ['sphinx', 'sphinx_rtd_theme']

# Allows developments build on Read the docs
if environ.get('READTHEDOCS_VERSION') == 'latest':
    for value in tuple(PACKAGE_INFO['install_requires']):
        if 'pycosio' in value:
            PACKAGE_INFO['install_requires'].remove(value)
            break
    PACKAGE_INFO['install_requires'] += ['pycosio']

# Generates wildcard "all" extras_require
PACKAGE_INFO['extras_require']['all'] = list(set(
    requirement for extra in PACKAGE_INFO['extras_require']
    for requirement in PACKAGE_INFO['extras_require'][extra]))
for key in tuple(PACKAGE_INFO['extras_require']['all']):
    # Force pycosio[all]
    if key.startswith('pycosio'):
        PACKAGE_INFO['extras_require']['all'].remove(key)
PACKAGE_INFO['extras_require']['all'].append('pycosio[all]')

# Gets Sphinx configuration
PACKAGE_INFO['command_options']['build_sphinx'] = {
    'project': ('setup.py', PACKAGE_INFO['name'].capitalize()),
    'version': ('setup.py', PACKAGE_INFO['version']),
    'release': ('setup.py', PACKAGE_INFO['version']),
    'copyright': ('setup.py', '2017-%s, %s' % (
        datetime.now().year, PACKAGE_INFO['author']))}

# Runs setup
if __name__ == '__main__':
    chdir(SETUP_DIR)
    setup(**PACKAGE_INFO)
