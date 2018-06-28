# coding=utf-8
"""Manages Accelerator and CSP configuration

Notes:
    The "accelerator.conf" file provided with this package can
    be used as sample for creation of your own configuration files.

    Use of this file is parameteral. All parameters can also be
    passed to API class. Non specified ones will use default values.

    API search automatically search for "accelerator.conf" in
    current working directory, or in current user home directory.
    A custom path to configuration file can also be passed
    to classes.
"""

from ast import literal_eval as _literal_eval
try:
    # Python 3
    from collections.abc import Mapping as _Mapping
except ImportError:
    # Python 2
    from collections import Mapping as _Mapping

import json as _json
import os.path as _os_path

from apyfal import exceptions as _exc
from apyfal import _utilities as _utl

#: Metering server URL
METERING_SERVER = 'https://master.metering.accelize.com'

#: Accelerator Executable path
ACCELERATOR_EXECUTABLE = '/opt/accelize/accelerator/accelerator'

__all__ = ['create_configuration', 'Configuration',
           'ACCELERATOR_EXECUTABLE',
           'accelerator_executable_available',
           'METERING_SERVER']


def create_configuration(configuration_file):
    """Create a configuration instance

    Args:
        configuration_file (str or Configuration or file-like object or None):
            Configuration file path or instance.
            Can Configuration instance or apyfal.storage URL,
            paths, file-like object"""
    if isinstance(configuration_file, Configuration):
        # configuration_file is already a Configuration instance
        return configuration_file
    return Configuration(configuration_file)


def accelerator_executable_available():
    """
    Returns True if accelerator executable available locally.

    Returns:
        bool: Accelerator executable found.
    """

    return _os_path.isfile(ACCELERATOR_EXECUTABLE)


class _Section(dict):
    """Configuration section

    Section that:
    - Returns None as default value if parameter not found
      (Don't raise KeyError).
    - Sets value only with non None value.

    Args:
        section_name (str): Section name in parent configuration file.
        section_parent (Configuration): Parent configuration file."""

    def __init__(self, section_name, section_parent, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        if '.' in section_name:

            self._default_section = section_name.split('.', 1)[0]
        else:
            self._default_section = None
        self._section_parent = section_parent

    def __missing__(self, section):
        # Always return None as default value
        return None

    def __setitem__(self, parameter, value):
        # Set new value only if not None
        if value is None:
            return
        dict.__setitem__(self, parameter, value)

    def __getitem__(self, parameter):
        # Try to get value directly in this section
        value = dict.__getitem__(self, parameter)

        # Try to get value in default section
        if value is None and self._default_section:
            return self._section_parent[
                self._default_section][parameter]
        return value

    def set(self, parameter, value=None):
        """Set value to parameter and return
        value.

        Args:
            parameter(str): Parameter to set.
            value(object): Value to set

        Returns:
            Return value if not None else
            already existing value in section."""
        self[parameter] = value
        return self[parameter]

    def get_literal(self, parameter):
        """
        Evaluate parameter str value to Python object
        and return it.

        Args:
            parameter (str): Parameter to get

        Returns:
            object: evaluated parameter
        """
        value = self[parameter]
        try:
            return _literal_eval(value)
        except (ValueError, TypeError, SyntaxError):
            return value


class Configuration(_Mapping):
    """Accelerator configuration.

    Mapping of configuration sections.
    On section access, never raises KeyError but returns at least
    an empty section.

    Sections are mapping of parameters. On parameter access, never raises
    KeyError but returns a default value of None.

    If a configuration section name contain dot (ex: "host.csp"),
    it is a subsection and accessing parameter performs
    the follow:
    - Tries to get parameter from this section ("host.csp")
    - If parameter value is None, tries to get value from
      parent section ("host")

    Trying to setting an parameter to None does nothing and keep
    previous value. Use "del" to delete an parameter to set a reset
    an parameter value.

    Args:
        configuration_file (str or file-like object or None):
            Configuration file path.
            Can be apyfal.storage URL, paths, file-like object.
            If None, use default values.
    """
    #: Default name for configuration file (Used for file detection)
    DEFAULT_CONFIG_FILE = "accelerator.conf"

    def __init__(self, configuration_file=None):
        _Mapping.__init__(self)

        # Initialize values Dictionaries
        self._sections = dict()
        self._cache = dict()

        # Finds configuration file
        if configuration_file is None:
            paths = (
                # Search configuration file in current working directory
                self.DEFAULT_CONFIG_FILE,
                # Search configuration file in home directory
                _os_path.join(_os_path.expanduser('~'), self.DEFAULT_CONFIG_FILE)
            )
            for path in paths:
                if _os_path.isfile(path):
                    configuration_file = path
                    break

        # Read configuration file if exists
        # If not, return empty Configuration file, this will force
        # host and accelerator classes to uses defaults values
        if configuration_file:
            # Initialize configuration parser
            # Lazy import since not used if no configuration file
            try:
                # Python 3
                from configparser import ConfigParser
                read_method = 'read_file'
            except ImportError:
                # Python 2
                from ConfigParser import ConfigParser
                read_method = 'readfp'
            ini_file = ConfigParser(allow_no_value=True)

            # Read from file with apyfal.storage support
            from apyfal.storage import open as srg_open
            with srg_open(configuration_file, 'rt') as file:
                getattr(ini_file, read_method)(file)

            # Retrieve parameters from configuration parser
            self._sections = {
                section: _Section(section, self, ini_file.items(section))
                for section in ini_file.sections()}

            # AcceleratorAPI backward compatibility
            self._legacy_backward_compatibility()

    def __getitem__(self, section):
        try:
            return self._sections.__getitem__(section)

        # Create missing empty section on first call
        except KeyError:
            self._sections[section] = _Section(section, self)
            return self._sections[section]

    def __contains__(self, section):
        return self._sections.__contains__(section)

    def __iter__(self):
        return self._sections.__iter__()

    def __len__(self):
        return self._sections.__len__()

    @property
    def _access_token(self):
        """
        Check user Accelize credential

        Returns:
            str: Access token.

        Raises:
            apyfal.exceptions.ConfigurationException:
                User credential are not valid.
        """
        try:
            return self._cache['metering_access_token']
        except KeyError:
            # Checks Client ID and secret ID presence
            client_id = self['accelize']['client_id']
            secret_id = self['accelize']['secret_id']
            if client_id is None or secret_id is None:
                raise _exc.ClientAuthenticationException(
                    exc="Accelize client ID and secret ID are mandatory.")

            # Check access and get token from server
            response = _utl.http_session().post(
                METERING_SERVER + '/o/token/',
                data={"grant_type": "client_credentials"},
                auth=(client_id, secret_id))

            if response.status_code != 200:
                raise _exc.ClientAuthenticationException(exc=response.text)

            self._cache['metering_access_token'] = _json.loads(
                response.text)['access_token']

        return self._cache['metering_access_token']

    def get_host_requirements(self, host_type, accelerator):
        """
        Gets accelerators requirements to use with host.

        Args:
            host_type (str): Host type.
            accelerator (str): Name of the accelerator

        Returns:
            dict: AcceleratorClient requirements for host.
        """
        headers = {"Authorization": "Bearer %s" % self._access_token,
                   "Content-Type": "application/json",
                   "Accept": "application/vnd.accelize.v1+json"}

        response = _utl.http_session().get(
            METERING_SERVER + '/auth/getlastcspconfiguration/',
            headers=headers)
        response.raise_for_status()
        response_config = _json.loads(response.text)

        # Get host_type configuration
        try:
            provider_config = response_config[host_type]
        except KeyError:
            raise _exc.ClientConfigurationException(
                "Host '%s' is not supported. Available hosts are: %s" % (
                    host_type, ', '.join(response_config.keys())))

        # Get accelerator configuration
        try:
            accelerator_config = provider_config[accelerator]
        except KeyError:
            raise _exc.ClientConfigurationException(
                "AcceleratorClient '%s' is not supported on '%s'." % (accelerator, host_type))

        accelerator_config['accelerator'] = accelerator
        return accelerator_config

    def _legacy_backward_compatibility(self):
        """
        Convert sections and parameters from legacy
        configuration files to current ones.
        """
        sections_changes = {'csp': 'host'}
        parameters_changes = {
            'csp': {
                'ssh_key': 'key_pair',
                'provider': 'host_type',
                'instance_ip': 'host_ip'
            }
        }
        # Fix sections
        for old, new in sections_changes.items():
            # Section to fix not exists
            if old not in self:
                continue

            # Warn user
            self._deprecation_warning(old)

            # Copy section
            for parameter, value in self[old].items():
                if parameter not in self[new]:
                    self[new][parameter] = value

            # Remove old section
            del self._sections[old]

        # Fix parameters
        for section, parameters in parameters_changes.items():
            new_section = sections_changes.get(section, section)
            if new_section not in self:
                continue

            for old, new in parameters.items():
                # Parameter to fix not exists
                if old not in self[new_section]:
                    continue

                # Warn user
                self._deprecation_warning(section, old)

                # Copy parameter
                if new not in self._sections[new_section]:
                    self[new_section][new] = self[new_section][old]

                # remove old parameter
                del self[new_section][old]

    @staticmethod
    def _deprecation_warning(section, parameter=''):
        """
        Warn user about deprecated section or
        parameter in configuration file.
        """
        import warnings
        warnings.warn(
            '"%s%s" is deprecated in "accelerator.conf"' %
            (section, ':%s' % parameter if parameter else ''),
            DeprecationWarning)
