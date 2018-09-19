# coding=utf-8
"""FPGA Host"""
from copy import deepcopy as _deepcopy
from datetime import datetime as _datetime
import re as _re

import apyfal.configuration as _cfg
import apyfal.exceptions as _exc
import apyfal._utilities as _utl


class Host(_utl.ABC):
    """This is base class for all host classes.

    This is also a factory which instantiate host subclass related to
    specified cases.

    Args:
        host_type (str): Host type.
        config (apyfal.configuration.Configuration, path-like object or file-like object):
            If not set, will search it in current working directory,
            in current user "home" folder. If none found, will use default
            configuration values.
            Path-like object can be path, URL or cloud object URL.
        host_name_prefix (str): Prefix to add to host name.
        host_ip (str): IP or URL address of an already existing host to use.
            If not specified, create a new host.
        stop_mode (str or int): Define the "stop" method behavior.
            Default to 'term' if new host, or 'keep' if already existing host.
            See "stop_mode" property for more information and possible values.
    """
    #: Host type name (str), must be the same as expected "host_type" argument
    # value
    NAME = None

    #: Link to host documentation or website
    DOC_URL = ''

    #: Possible stop_mode int values
    STOP_MODES = {0: "term", 1: "stop", 2: "keep"}

    #: Timeout for host status change in seconds
    TIMEOUT = 420.0

    # Attributes returned as dict by "info" property
    _INFO_NAMES = {'_host_type', '_stop_mode', '_url', '_host_name'}

    # Value to show in repr
    _REPR = [('type', '_host_type'), ('name', '_host_name')]

    # Prefix for default parameter value (see "_default_parameter_value")
    _PARAMETER_PREFIX = 'Accelize'

    def __new__(cls, *args, **kwargs):
        # If call from a subclass, instantiate this subclass directly
        if cls is not Host:
            return object.__new__(cls)

        # Get host_type from configuration or argument
        config = _cfg.create_configuration(kwargs.get('config'))
        host_type = cls._host_type_from_config(
            _utl.get_first_arg(args, kwargs, 'host_type'), config)

        # Get host subclass
        return _utl.factory(
            cls, host_type, 'host_type', _exc.HostConfigurationException)

    def __init__(self, host_type=None, config=None, host_ip=None,
                 stop_mode=None, host_name_prefix=None, **_):

        # Default some attributes
        self._cache = {}
        self._accelerator = None
        self._stop_mode = None
        self._config_env = {}
        self._config_section = 'host.%s' % self.NAME if self.NAME else 'host'
        self._host_name = None
        self._host_name_match = None

        # Read configuration from file
        self._config = _cfg.create_configuration(config)
        section = self._config[self._config_section]

        self._host_type = self._host_type_from_config(host_type, self._config)

        self._url = _utl.format_url(host_ip or section['host_ip'])

        self.stop_mode = (stop_mode or section['stop_mode'] or
                          ('keep' if host_ip else 'term'))

        self._host_name_prefix = (host_name_prefix or
                                  section['host_name_prefix'] or '')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.stop()

    def __del__(self):
        self.stop()

    def __str__(self):
        return "<%s.%s %s>" % (
            self.__class__.__module__, self.__class__.__name__, ' '.join(
                "%s='%s'" % (name, getattr(self, attr))
                for name, attr in self._REPR
                if getattr(self, attr) is not None))

    __repr__ = __str__

    @property
    def host_type(self):
        """
        Host type

        Returns:
            str: Host type
        """
        return self._host_type

    @property
    def url(self):
        """
        URL of the current host.

        Returns:
            str: URL
        """
        # Returns URL
        return self._url

    @property
    def host_name(self):
        """
        Name of the current host.

        Returns:
            str: Name
        """
        return self._get_host_name()

    @property
    def stop_mode(self):
        """
        Define the "stop" method behavior.

        Possible values ares:
            0: TERM, terminate and delete host.
            1: STOP, stop and pause host.
            2: KEEP, let host running.

        "stop" can be called manually but is also called when:
            - "with" exit if class is used as context manager.
            - On object deletion by garbage collector.
            - On OS signals if "exit_host_on_signal" was set to True
              on class instantiation.

        Returns:
            str: stop mode.
        """
        return self._stop_mode

    @stop_mode.setter
    def stop_mode(self, stop_mode):
        """
        Set stop_mode.

        Args:
            stop_mode (str or int): stop mode value to set
        """
        if stop_mode is None:
            return

        # Converts from int values
        try:
            stop_mode = int(stop_mode)
        except (TypeError, ValueError):
            pass

        if isinstance(stop_mode, int):
            stop_mode = self.STOP_MODES.get(stop_mode, '')

        # Checks value
        stop_mode = stop_mode.lower()
        if stop_mode not in self.STOP_MODES.values():
            raise ValueError(
                "Invalid value %s, Possible values are %s" % (
                    stop_mode, ', '.join(
                        value for value in self.STOP_MODES.values())))

        self._stop_mode = stop_mode

    def start(self, accelerator=None, accel_parameters=None, stop_mode=None):
        """
        Start host if not already started.

        Needs "accel_client" or "accel_parameters".

        Args:
            accelerator (str): Name of the accelerator.
            accel_parameters (dict): Can override parameters from accelerator
                client.
            stop_mode (str or int): See "stop_mode" property for more
                information.
        """
        # Check configuration
        if not self._url:
            raise _exc.HostConfigurationException(gen_msg='no_host_found')

        # Update stop mode
        self.stop_mode = stop_mode

    @property
    def info(self):
        """
        Returns some host information.

        Returns:
            dict: Dictionary containing information on
                current host.
        """
        info = {}
        for name in self._INFO_NAMES:
            try:
                value = getattr(self, name)
            except (AttributeError, _exc.HostException):
                continue
            info[name.strip('_')] = value
        return info

    def stop(self, stop_mode=None):
        """
        Stop host accordingly with the current stop_mode.
        See "stop_mode" property for more information.

        Args:
            stop_mode (str or int): If not None, override current "stop_mode"
                value.
        """

    def _set_accelerator_requirements(
            self, accelerator=None, accel_parameters=None):
        """
        Configures instance with accelerator client parameters.

        Needs "accel_client" or "accel_parameters".

        Args:
            accelerator (str): Name of the accelerator
            accel_parameters (dict): Can override parameters from accelerator
                client.

        Raises:
            apyfal.exceptions.HostConfigurationException:
                Parameters are not valid..
        """
        # Gets parameters
        parameters = dict()
        if accelerator is not None:
            _utl.recursive_update(
                parameters, self._config.get_host_requirements(
                    self._host_type, accelerator))

        if accel_parameters is not None:
            _utl.recursive_update(
                parameters, _deepcopy(accel_parameters))

        # Gets accelerator name
        self._accelerator = parameters.pop('accelerator')

        # Gets parameters for current region
        self._config_env = parameters

    def get_configuration_env(self, **config_env):
        """
        Return environment to pass to
        "apyfal.accelerator.AcceleratorClient.start"
        "csp_env" argument.

        Args:
            config_env: Overwrites environment values.

        Returns:
            dict: Configuration environment.
        """
        if not config_env:
            # Returns default environment
            return self._config_env

        current_env = _deepcopy(self._config_env)
        current_env.update(config_env)

        # Old name backward compatibility
        try:
            current_env['fpgaimage'] = config_env['AGFI']
        except KeyError:
            pass

        return current_env

    @classmethod
    def _host_type_from_config(cls, host_type, config):
        """
        Get host type from configuration.

        Args:
            host_type (str): Override result if not None.
            config (apyfal.configuration.Configuration): Configuration.

        Returns:
            str: host type.

        Raises:
            apyfal.exceptions.HostConfigurationException: No host_type found.
        """
        host_type = host_type or config['host']['host_type']
        if not host_type:
            # Use default value if any
            host_type = cls.NAME
        return host_type

    def _check_arguments(self, *arg_name):
        """
        Check in attributes if arguments are set.

        Args:
            arg_name (str): Argument names to check.

        Raises:
            apyfal.exceptions.HostConfigurationException:
                A specified argument is None.
        """
        for name in arg_name:
            if getattr(self, '_%s' % name) is None:
                raise _exc.HostConfigurationException(
                    "Parameter '%s' is required %s" % (name, self._host_type))

    @classmethod
    def _default_parameter_value(cls, parameter_name, include_host=False):
        """
        Returns a CamelCase name for default parameter
        value.

        Args:
            parameter_name (str): Name of parameter
            include_host (bool): If True, include host_type name in name.

        Returns:
            str: default parameter value.
        """
        return ''.join((cls._PARAMETER_PREFIX, cls.NAME if include_host else '',
                        parameter_name))

    @classmethod
    def _add_help_to_exception_message(cls, exception):
        """
        Improve exception message by adding host specific help indication.

        Args:
            exception (Exception): exception.
        """
        if cls.DOC_URL:
            args = list(exception.args)
            args[0] = '%s, please refer to: %s' % (
                args[0].rstrip('.'), cls.DOC_URL)
            exception.args = tuple(args)

    def _get_host_name(self):
        """Returns name to use as host name

        Returns:
            str: name with format
                '<Prefix>_accelize_<AcceleratorName>_<DateTime>'"""
        if self._host_name is None:

            self._host_name = '_'.join(
                name for name in (
                    # Add user and "accelize" prefix
                    self._host_name_prefix, 'accelize',

                    # Name is based on accelerator Name
                    # '@' is used in some testing configurations but is a
                    # forbidden character for name on some host types
                    self._accelerator.replace('@', '_'),

                    # Add date and time to have unique name
                    _datetime.now().strftime('%y%m%d%H%M%S')) if name)

        return self._host_name

    def _iter_hosts(self):
        """
        Iterates over accelerator hosts of current type.

        Returns:
            generator of dict: dicts contains attributes values of the host.
        """
        # Empty generator by default
        return iter(())

    def _is_accelerator_host(self, host_name):
        """
        Checks if host is an accelerator host.

        Only indented to be run from "_iter_hosts".

        Args:
            host_name (str): Host name

        Returns:
            bool: True if accelerator host.
        """
        result = self._host_name_match(host_name)
        if result and result.end() - result.start() == len(host_name):
            return True
        return False

    def iter_hosts(self, host_name_prefix=True):
        """
        Iterates over accelerator hosts of current type.

        Args:
            host_name_prefix (bool or str): If True,
                use "host_name_prefix" from configuration, if False
                don't filter by prefix, if str, uses this str as prefix

        Returns:
            generator of dict: dicts contains attributes values of the host.
        """
        # Prepares name validator
        if host_name_prefix is True:
            # Use configuration prefix
            host_name_prefix = self._host_name_prefix

        elif host_name_prefix is False:
            # Show instances with all prefixes
            host_name_prefix = '.*'

        if host_name_prefix not in ('', '.*'):
            # Adds separator
            host_name_prefix += '_'

        self._host_name_match = _re.compile(
            '%saccelize_\w*_\d{12}' % host_name_prefix).match

        # Prepares repr base information
        repr_base = "<%s.%s" % (self.__class__.__module__,
                                self.__class__.__name__) + ' %s>'
        repr_list = [(name, attr.lstrip('_')) for name, attr in self._REPR]

        # Validates and yield hosts
        for host in self._iter_hosts():

            # Completes host information
            host['host_type'] = self._host_type
            host['accelerator'] = host['host_name'].split(
                'accelize_', 1)[1].rsplit('_', 1)[0]
            if 'public_ip' in host:
                host['url'] = _utl.format_url(host['public_ip'])

            # Adds host repr
            host['_repr'] = repr_base % (' '.join(
                "%s='%s'" % (name, host.get(attr)) for name, attr in
                repr_list
                if host.get(attr) is not None))

            yield host
