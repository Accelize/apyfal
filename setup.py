#! /usr/bin/env python
#  coding=utf-8
"""Accelerator API setup script

run "./setup.py --help-commands" for help.
"""
from datetime import datetime
from os import makedirs, chdir
from os.path import dirname, abspath, join, isfile, isdir
from sys import argv

from setuptools import setup, find_packages, Command

# Sets Package information
PACKAGE_INFO = dict(
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
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Operating System :: OS Independent'
        ],
    keywords='fpga cloud accelerator accelize',
    author='Accelize',
    author_email='info@accelize.com',
    url='https://github.com/Accelize/acceleratorAPI',
    project_urls={
        'AccelStore': 'https://accelstore.accelize.com/',
        'Accelize Website': 'https://www.accelize.com/',
        'Contact': 'https://www.accelize.com/contact-us/'
    },
    license='Apache',
    python_requires='>=2.7,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*',
    install_requires=['setuptools', 'requests', 'ipgetter'],
    extras_require={
        # Optional speedup
        'optional': ['pycurl'],

        # CSP specific requirements
        'AWS': ['boto3'],
        'OVH': ['openstacksdk']},
    setup_requires=['setuptools'],
    tests_require=['pytest'],
    packages=find_packages(exclude=['docs', 'tests', 'rest_api']),
    include_package_data=True,
    zip_safe=True,
    command_options={},
    cmdclass={}
    )

# Gets package __version__ from package
SETUP_DIR = abspath(dirname(__file__))
with open(join(SETUP_DIR, 'acceleratorAPI', '__init__.py')) as source_file:
    for line in source_file:
        if line.rstrip().startswith('__version__'):
            PACKAGE_INFO['version'] = line.split('=', 1)[1].strip(" \"\'\n")
            break

# Gets long description from readme
with open(join(SETUP_DIR, 'README.md')) as source_file:
    PACKAGE_INFO['long_description'] = source_file.read()

# Add command to generate REST API with Swagger-Codegen
REST_API_BUILD_DIR = join(SETUP_DIR, 'build', 'rest_api')
REST_API_GENERATED_DIR = join(REST_API_BUILD_DIR, 'output')
REST_API_SETUP = join(REST_API_GENERATED_DIR, 'setup.py')


class SwaggerCommand(Command):
    """
    Generate Python REST API client using Swagger-Codegen
    """
    description = "Generate REST API client (acceleratorAPI/_swagger_client)"
    user_options = [
        ('swagger-version=', None, 'Force use of a specific Swagger-Codegen version'),
    ]

    def initialize_options(self):
        """Options default values"""
        self.swagger_version = ''

    def finalize_options(self):
        """Validate options values"""

    def run(self):
        """Run Swagger command"""
        # Lazzy import since required only here
        import json
        from shutil import copytree, rmtree
        from subprocess import Popen
        try:
            # Python 3
            from urllib.request import urlopen, urlretrieve
        except ImportError:
            # Python 2
            from urllib import urlopen, urlretrieve
        from xml.etree import ElementTree

        # Define paths
        repository = ('https://oss.sonatype.org/content/repositories/'
                      'releases/io/swagger/swagger-codegen-cli')
        src_dir = join(SETUP_DIR, 'rest_api')
        input_spec_path = join(src_dir, 'input_spec.json')

        # Create output directory, if needed
        try:
            makedirs(REST_API_GENERATED_DIR)
        except OSError:
            if not isdir(REST_API_GENERATED_DIR):
                raise

        # Get last Swagger version if not specified
        if not self.swagger_version:
            # Get project OpenAPI version
            with open(input_spec_path, 'rt') as input_spec_file:
                input_spec = json.load(input_spec_file)
            openapi_version = int(input_spec['swagger'][0])

            # Get Maven metadata from repository
            maven_metadata = ElementTree.fromstring(
                urlopen('%s/maven-metadata.xml' % repository).read())

            # Get the last release version
            version = maven_metadata.findall('versioning/release')[0].text

            # If not the same OpenAPI version in last release and project
            # find the last compatible version
            if int(version[0]) > openapi_version:
                versions = reversed([
                    version.text for version in
                    maven_metadata.findall('versioning/versions/version')])

                for version in versions:
                    if int(version[0]) == openapi_version:
                        break

            self.swagger_version = version

        print('Using Swagger-Codegen %s' % self.swagger_version)

        jar_name = 'swagger-codegen-cli-%s.jar' % self.swagger_version
        jar_path = join(REST_API_BUILD_DIR, jar_name)

        # Download Swagger-codegen Jar if needed
        if not isfile(jar_path):
            print('Downloading %s' % jar_name)
            urlretrieve('/'.join((repository, self.swagger_version, jar_name)), jar_path)

        # Clear output directory
        print('Clearing %s' % REST_API_GENERATED_DIR)
        rmtree(REST_API_GENERATED_DIR, ignore_errors=True)

        # Run Swagger-codegen
        command = ' '.join([
                "java", "-jar", jar_path, "generate",
                "-i", input_spec_path,
                "-o", REST_API_GENERATED_DIR,
                "-l", "python"])
        print('Running command "%s"' % command)
        Popen(command, shell=True).communicate()

        # Fix generated source code
        from os import walk
        for root, _, files in walk(join(REST_API_GENERATED_DIR, 'swagger_client')):
            for file_name in files:
                file_path = join(root, file_name)
                with open(file_path, 'rt') as file_handle:
                    content = file_handle.read()

                # Fix imports
                replacements = [
                    ('from swagger_client', 'from acceleratorAPI._swagger_client'),
                    ('import swagger_client', 'import acceleratorAPI._swagger_client'),
                    ('getattr(swagger_client.', 'getattr(acceleratorAPI._swagger_client.'),
                ]

                # Fix Swagger bug:
                # https://github.com/swagger-api/swagger-codegen/pull/7684
                # TODO: Remove once fixed in released Swagger-Codegen version
                for value in ('1', '2', '3', '4', ''):
                    replacements.append((
                        'swagger_client.models.inline_response200%s' % value,
                        'swagger_client.models.inline_response_200%s' %
                        (('_%s' % value) if value else '')))

                # Replace in file
                for before, after in replacements:
                    content = content.replace(before, after)

                with open(file_path, 'wt') as file_handle:
                    file_handle.write(content)

        # Move Result to acceleratorAPI/rest_api
        rest_api_dst = join(SETUP_DIR, 'acceleratorAPI', '_swagger_client')
        print('Clearing %s' % rest_api_dst)
        rmtree(rest_api_dst, ignore_errors=True)

        rest_api_src = join(REST_API_GENERATED_DIR, 'swagger_client')
        print('Copying REST API from %s to %s' % (rest_api_src, rest_api_dst))
        copytree(rest_api_src, rest_api_dst)


PACKAGE_INFO['cmdclass']['swagger_codegen'] = SwaggerCommand

# Gets requirements from Swagger generated REST API
if 'swagger_codegen' not in argv:
    if not isfile(REST_API_SETUP):
        raise RuntimeError(
            "REST API not generated, "
            "please run 'setup.py swagger_codegen' first")

    from ast import literal_eval
    with open(REST_API_SETUP) as source_file:
        for line in source_file:
            if line.rstrip().startswith('REQUIRES = ['):
                PACKAGE_INFO['install_requires'].extend(
                    literal_eval(line.split('=', 1)[1].strip(" \n")))
                break

# Add pytest_runner requirement if needed
if {'pytest', 'test', 'ptr'}.intersection(argv):
    PACKAGE_INFO['setup_requires'].append('pytest-runner')

# Add Sphinx requirements if needed
elif 'build_sphinx' in argv:
    PACKAGE_INFO['setup_requires'] += [
        'sphinx', 'recommonmark', 'sphinx_rtd_theme']

# Generates wildcard "all" extras_require
PACKAGE_INFO['extras_require']['all'] = list(set(
    requirement for extra in PACKAGE_INFO['extras_require']
    for requirement in PACKAGE_INFO['extras_require'][extra]
    ))

# Gets Sphinx configuration
PACKAGE_INFO['command_options']['build_sphinx'] = {
    'project': ('setup.py', PACKAGE_INFO['name'].capitalize()),
    'version': ('setup.py', PACKAGE_INFO['version']),
    'release': ('setup.py', PACKAGE_INFO['version']),
    'copyright': ('setup.py', '2017-%s, %s' % (
        datetime.now().year, PACKAGE_INFO['author'])),
    }

# Runs setup
if __name__ == '__main__':
    chdir(SETUP_DIR)
    setup(**PACKAGE_INFO)
