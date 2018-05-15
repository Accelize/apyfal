# coding=utf-8
"""Accelerator API setup script"""
from datetime import datetime
from ast import literal_eval
from os.path import dirname, abspath, join
from setuptools import setup, find_packages

# Sets Package information
PACKAGE_INFOS = dict(
    name='acceleratorAPI',
    description='Accelize AcceleratorAPI is a powerful and flexible '
                'toolkit for testing and operate FPGA accelerated function.',
    long_description_content_type='text/markdown; charset=UTF-8',
    classifiers=[
        # Must be listed on: https://pypi.org/classifiers/
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Topic :: Other/Nonlisted Topic',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Operating System :: OS Independent'
        ],
    keywords='fpga cloud accelerator accelize',
    author='Accelize',
    author_email='https://www.accelize.com/contact-us/',
    url='https://github.com/Accelize/acceleratorAPI',
    project_urls={
        'AccelStore': 'https://accelstore.accelize.com/',
        'Accelize Website': 'https://www.accelize.com/',
        'Contact': 'https://www.accelize.com/contact-us/'
    },
    license='Apache',
    python_requires='==2.7',
    install_requires=['setuptools', 'requests'],
    extras_require={
        # Optional speedup
        'optional': ['pycurl'],

        # CSP specific requirements
        'AWS': ['boto3'],
        'OVH': ['openstack']},
    setup_requires=['pytest', 'sphinx', 'setuptools', 'recommonmark', 'sphinx_rtd_theme'],
    packages=find_packages(exclude=['docs', 'tests', '*.test']),
    include_package_data=True,
    zip_safe=True,
    command_options={},
    )

# Gets package __version__ from package
SETUP_DIR = abspath(dirname(__file__))
with open(join(SETUP_DIR, 'acceleratorAPI', '__init__.py')) as source_file:
    for line in source_file:
        if line.rstrip().startswith('__version__'):
            PACKAGE_INFOS['version'] = line.split('=', 1)[1].strip(" \"\'\n")
            break

# Gets long description from readme
with open(join(SETUP_DIR, 'README.md')) as source_file:
    PACKAGE_INFOS['long_description'] = source_file.read()

# Gets requirements from Swagger generated REST API
with open(join(SETUP_DIR, 'acceleratorAPI', 'rest_api', 'setup.py')) as source_file:
    for line in source_file:
        if line.rstrip().startswith('REQUIRES = ['):
            PACKAGE_INFOS['install_requires'].extend(
                literal_eval(line.split('=', 1)[1].strip(" \n")))
            break

# Generates wildcard "all" extras_require
PACKAGE_INFOS['extras_require']['all'] = list(set(
    requirement for extra in PACKAGE_INFOS['extras_require']
    for requirement in PACKAGE_INFOS['extras_require'][extra]
    ))

# Gets Sphinx configuration
PACKAGE_INFOS['command_options']['build_sphinx'] = {
    'project': ('setup.py', PACKAGE_INFOS['name'].capitalize()),
    'version': ('setup.py', PACKAGE_INFOS['version']),
    'release': ('setup.py', PACKAGE_INFOS['version']),
    'copyright': ('setup.py', '2017-%s, %s' % (
        datetime.now().year, PACKAGE_INFOS['author'])),
    }

# Runs setup
if __name__ == '__main__':
    from os import chdir
    chdir(SETUP_DIR)
    setup(**PACKAGE_INFOS)
