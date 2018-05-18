# coding=utf-8
"""Accelerator API setup script"""
from datetime import datetime
from ast import literal_eval
from os import makedirs, chdir
from os.path import dirname, abspath, join, isfile, isdir
from shutil import copytree, rmtree
from subprocess import Popen
from sys import argv
try:
    # Python 3
    from urllib.request import urlopen, urlretrieve
except ImportError:
    # Python 2
    from urllib import urlopen, urlretrieve
from xml.etree import ElementTree

from setuptools import setup, find_packages, Command



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
    author_email='info@accelize.com',
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
            PACKAGE_INFOS['version'] = line.split('=', 1)[1].strip(" \"\'\n")
            break

# Gets long description from readme
with open(join(SETUP_DIR, 'README.md')) as source_file:
    PACKAGE_INFOS['long_description'] = source_file.read()


# Add command to generate REST API with Swagger-Codegen
REST_API_BUILD_DIR = join(SETUP_DIR, 'build', 'rest_api')
REST_API_GENERATED_DIR = join(REST_API_BUILD_DIR, 'output')
REST_API_SETUP = join(REST_API_GENERATED_DIR, 'setup.py')


class SwaggerCommand(Command):
    """
    Generate Python REST API Client using Swagger-Codegen
    """
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
        repository = ('https://oss.sonatype.org/content/repositories/'
                      'releases/io/swagger/swagger-codegen-cli')
        src_dir = join(SETUP_DIR, 'rest_api')

        # Create output directory, if needed
        try:
            makedirs(REST_API_GENERATED_DIR)
        except OSError:
            if not isdir(REST_API_GENERATED_DIR):
                raise

        # Get last Swagger version if not specified
        if not self.swagger_version:
            response = urlopen('%s/maven-metadata.xml' % repository)
            xml = ElementTree.fromstring(response.read())
            self.swagger_version = xml.findall('versioning/release')[0].text

        jar_name = 'swagger-codegen-cli-%s.jar' % self.swagger_version
        jar_path = join(REST_API_BUILD_DIR, jar_name)

        # Download Swagger-codegen Jar if needed
        if not isfile(jar_path):
            urlretrieve('/'.join((repository, self.swagger_version, jar_name)), jar_path)

        # Run Swagger-codegen
        rmtree(REST_API_GENERATED_DIR, ignore_errors=True)
        command = ' '.join([
                "java", "-jar", jar_path, "generate",
                "-c", join(src_dir, 'config.json'),
                "-i", join(src_dir, 'input_spec.json'),
                "-o", REST_API_GENERATED_DIR,
                "-l", "python"])
        Popen(command, shell=True).communicate()

        # Move Result to acceleratorAPI/rest_api
        rest_api_dir = join(SETUP_DIR, 'acceleratorAPI', 'rest_api')
        rmtree(rest_api_dir, ignore_errors=True)
        copytree(join(REST_API_GENERATED_DIR, 'swagger_client'), rest_api_dir)


PACKAGE_INFOS['cmdclass']['swagger_codegen'] = SwaggerCommand

# Gets requirements from Swagger generated REST API
if 'swagger_codegen' not in argv:
    if not isfile(REST_API_SETUP):
        raise RuntimeError(
            "REST API not generated, "
            "please run 'setup.py swagger_codegen' first")

    with open(REST_API_SETUP) as source_file:
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
