# coding=utf-8
"""FPGA Host"""

import apyfal.configuration as _cfg
import apyfal.exceptions as _exc
import apyfal._utilities as _utl


class Host(_utl.ABC):
    """This is base class for all host classes.

    This is also a factory which instantiate host subclass related to
    specified cases.

    Args:
        host_type (str): Host type.
        config (str or apyfal.configuration.Configuration): Configuration file path or instance.
            If not set, will search it in current working directory, in current
            user "home" folder. If none found, will use default configuration values.
        host_ip (str): IP or URL address of an already existing host to use.
            If not specified, create a new host.
        stop_mode (str or int): Define the "stop" method behavior.
            Default to 'term' if new host, or 'keep' if already existing host.
            See "stop_mode" property for more information and possible values.
        exit_host_on_signal (bool): If True, exit host
            on OS exit signals. This may help to not have host still running
            if Python interpreter is not exited properly. Note: this is provided for
            convenience and does not cover all exit case like process kill and
            may not work on all OS.
    """
    #: Host type name (str), must be the same as expected "host_type" argument value
    NAME = None

    #: Link to host documentation or website
    DOC_URL = ''

    #: Possible stop_mode int values
    STOP_MODES = {
        0: "term",
        1: "stop",
        2: "keep"}
    #: Timeout for host status change in seconds
    TIMEOUT = 360.0

    # Attributes returned as dict by "info" property
    _INFO_NAMES = {'_host_type', '_stop_mode', '_url'}

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
                 stop_mode=None, exit_host_on_signal=False, **_):

        # Default some attributes
        self._accelerator = None
        self._stop_mode = None
        self._config_section = 'host.%s' % self.NAME if self.NAME else 'host'

        # Read configuration from file
        self._config = _cfg.create_configuration(config)
        section = self._config[self._config_section]

        self._host_type = self._host_type_from_config(host_type, self._config)

        self._url = _utl.format_url(host_ip or section['host_ip'])

        self.stop_mode = (
            stop_mode or section['stop_mode'] or
            ('keep' if host_ip else 'term'))

        # Enable optional Signal handler
        self._set_signals(exit_host_on_signal)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.stop()

    def __del__(self):
        self.stop()

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
            accel_parameters (dict): Can override parameters from accelerator client.
            stop_mode (str or int): See "stop_mode" property for more information.
        """
        # Check configuration
        if not self._url:
            raise _exc.HostConfigurationException(
                'No host found. Please check your configuration.')

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
            stop_mode (str or int): If not None, override current "stop_mode" value.
        """

    def get_configuration_env(self, **_):
        """
        Return environment to pass to
        "apyfal.client.AcceleratorClient.start" "host_env" argument.

        Returns:
            dict: Configuration environment.
        """
        return self._config_env

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

    def _set_signals(self, exit_host_on_signal=True):
        """
        Set a list of interrupt signals to be handled asynchronously to emergency stop
        host in case of unexpected exit.

        Args:
            exit_host_on_signal (bool): If True, enable stop on signals.
        """
        if not exit_host_on_signal:
            return

        # Lazy import since optional feature
        import signal

        for signal_name in ('SIGTERM', 'SIGINT', 'SIGQUIT'):
            # Check signal exist on current OS before setting it
            if hasattr(signal, signal_name):
                signal.signal(getattr(signal, signal_name), self.stop)

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
        return 'Accelize%s%s' % (cls.NAME if include_host else '', parameter_name)

    @classmethod
    def _add_csp_help_to_exception_message(cls, exception):
        """
        Improve exception message by adding CSP help indication.

        Args:
            exception (Exception): exception.
        """
        if cls.DOC_URL:
            args = list(exception.args)
            args[0] = '%s, please refer to: %s' % (args[0].rstrip('.'), cls.DOC_URL)
            exception.args = tuple(args)
