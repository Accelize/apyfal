"""Manages Accelerator and CSP configuration"""
import os
try:
    # Python 3
    import configparser as _configparser
except ImportError:
    # Python 2
    import ConfigParser as _configparser


def create_configuration(configuration_file, **kwargs):
    """Create a configuration instance

    Args:
        configuration_file (str or Configuration): Configuration file path or instance.
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
            if os.path.isfile(self.DEFAULT_CONFIG_FILE):
                # Search configuration file in current working directory
                configuration_file = self.DEFAULT_CONFIG_FILE
            else:
                # Get default file in package directory
                configuration_file = os.path.join(os.path.dirname(__file__), self.DEFAULT_CONFIG_FILE)

        # Read configuration file
        if not self.read(configuration_file):
            # No file read
            raise IOError("Could not find configuration file: %s" % os.path.abspath(configuration_file))

        self._file_path = configuration_file

    @property
    def file_path(self):
        """Configuration file path

        Returns:
            path (str)"""
        return self._file_path

    def get_default(self, section, option, overwrite=None, default=None):
        """Returns values from configuration or default value.

        Args:
            section (str): Configuration section
            option (str): Key in selected section
            overwrite: If None not, forces return of this value
            default: If section or key not found, return this value.
        Returns:
            value (object)
            """
        if overwrite is not None:
            return overwrite

        try:
            new_val = self.get(section, option)
        except (_configparser.NoSectionError, _configparser.NoOptionError):
            return default

        if new_val:
            return new_val
        return default

    def is_valid(self, *section_option):
        """
        For each section_key pairs, check if value exists in configuration
        and if value if not empty.

        Args:
            *section_option (tuple of str): section option pairs.

        Returns:
            bool: True if all values exists and are not empty, False elsewhere.
        """
        for section, option in section_option:
            try:
                value = self.get(section, option)
            except (_configparser.NoSectionError, _configparser.NoOptionError):
                return False
            if not value:
                return False
        return True

    def set_not_none(self, section, option, value):
        """
        Set value for selected section and option if value is not None.

        Args:
            section (str): Configuration section
            option (str): Configuration option
            value: value"""
        if value is not None:
            self._config.set(section, option, value)
