# coding=utf-8
"""Manages Accelerator and CSP configuration

Notes:
    The "accelerator.conf" file provided with this package can
    be used as sample for creation of your own configuration files.

    Use of this file is optional. All parameters can also be
    passed to API class. Non specified ones will use default values.

    API search automatically search for "accelerator.conf" in
    current working directory, or in current user home directory.
    A custom path to configuration file can also be passed
    to classes.
"""

import os.path as _os_path
from ast import literal_eval as _literal_eval
try:
    # Python 3
    import configparser as _configparser
except ImportError:
    # Python 2
    import ConfigParser as _configparser

# Constants
METERING_SERVER = 'https://master.metering.accelize.com'


def create_configuration(configuration_file, **kwargs):
    """Create a configuration instance

    Args:
        configuration_file (str or Configuration or None):
            Configuration file path or instance.
        kwargs: "configparser.ConfigParser" keyword arguments.
                Ignored if configuration_file is already a Configuration instance"""
    if isinstance(configuration_file, Configuration):
        # configuration_file is already a Configuration instance
        return configuration_file
    return Configuration(configuration_file, **kwargs)


class Configuration(_configparser.ConfigParser):
    """Accelerator configuration

    Args:
        configuration_file (str): Configuration file path.
        kwargs: "configparser.ConfigParser" keyword arguments"""
    DEFAULT_CONFIG_FILE = "accelerator.conf"

    def __init__(self, configuration_file=None, **kwargs):
        # Initializes parent class but force allow_no_value
        kwargs['allow_no_value'] = True
        _configparser.ConfigParser.__init__(self, **kwargs)

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
        # CSP and accelerator classes to uses defaults values
        if configuration_file:
            self.read(configuration_file)

    def get_default(self, section, option, overwrite=None, default=None, is_literal=False):
        """Returns values from configuration or default value.

        Args:
            section (str): Configuration section
            option (str): Key in selected section
            overwrite: If None not, forces return of this value
            default: If section or key not found, return this value.
            is_literal (bool): If True evaluated as literal.
        Returns:
            value (object)
            """
        if overwrite is not None:
            return overwrite

        try:
            new_val = self.get(section, option)
        except (_configparser.NoSectionError, _configparser.NoOptionError):
            return default

        if not new_val:
            return default

        elif is_literal:
            return _literal_eval(new_val)
        return new_val

    def has_accelize_credential(self):
        """
        Check if Accelize credentials are present in configuration file.

        Returns:
            bool: True if credentials founds in file.
        """
        return (self.get_default('accelize', 'client_id') and
                self.get_default('accelize', 'secret_id'))

    def has_csp_credential(self):
        """
        Check if CSP credentials are present in configuration file.

        Returns:
            bool: True if credentials founds in file.
        """
        return (self.get_default('csp', 'client_id') and
                self.get_default('csp', 'secret_id'))
