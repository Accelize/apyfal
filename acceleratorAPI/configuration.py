"""Manages Accelerator and CSP configuration"""
import os
try:
    # Python 3
    import configparser as _configparser
except ImportError:
    # Python 2
    import ConfigParser as _configparser


class Configuration(_configparser.ConfigParser):
    """Accelerator configuration

    Args:
        file_path (str): Optional configuration file path.
        kwargs: "configparser.ConfigParser" keyword arguments"""
    DEFAULT_CONFIG_FILE = "accelerator.conf"

    def __init__(self, file_path=None, **kwargs):

        kwargs['allow_no_value'] = True
        _configparser.ConfigParser.__init__(self, **kwargs)

        # Find configuration file
        if file_path is None:
            if os.path.isfile(self.DEFAULT_CONFIG_FILE):
                # Search configuration file in current working directory
                file_path = self.DEFAULT_CONFIG_FILE
            else:
                # Get default file in package directory
                file_path = os.path.join(os.path.dirname(__file__), self.DEFAULT_CONFIG_FILE)

        if not os.path.isfile(file_path):
            raise IOError("Could not find configuration file: %s" % file_path)

        # Load file
        self.read(file_path)
        self._file_path = file_path

    @property
    def file_path(self):
        """Configuration file path

        Returns:
            path (str)"""
        return self._file_path

    def get_default(self, section, key, overwrite=None, default=None):
        """Returns values from configuration of default value.

        Args:
            section (str): Configuration section
            key (str): Key in selected section
            overwrite: If None not, forces return of this value
            default: If section or key not found, return this value.
        Returns:
            value (object)
            """
        if overwrite is not None:
            return overwrite

        try:
            new_val = self.get(section, key)
        except (_configparser.NoSectionError, _configparser.NoOptionError):
            return default

        if new_val:
            return new_val
        return default
