# coding=utf-8
"""Cloud Service Providers"""

from abc import abstractmethod as _abstractmethod
from importlib import import_module as _import_module

import acceleratorAPI.configuration as _cfg
import acceleratorAPI.exceptions as _exc
import acceleratorAPI._utilities as _utl
from acceleratorAPI._utilities import get_logger as _get_logger


class CSPGenericClass(_utl.ABC):
    """This is base abstract class for all CSP classes.

    This is also a factory which instantiate CSP subclass related to
    specified Cloud Service Provider.

    Args:
        provider (str): Cloud service provider name.
        config (str or acceleratorAPI.configuration.Configuration): Configuration file path or instance.
            If not set, will search it in current working directory, in current
            user "home" folder. If none found, will use default configuration values.
        client_id (str): CSP Access Key ID.
        secret_id (str): CSP Secret Access Key.
        region (str): CSP region. Needs a region supporting instances with FPGA devices.
        instance_type (str): CSP instance type. Default defined by accelerator.
        ssh_key (str): CSP Key pair. Default to 'Accelize<CSPNAME>KeyPair'.
        security_group: CSP Security group. Default to 'AccelizeSecurityGroup'.
        instance_id (str): Instance ID of an already existing CSP instance to use.
            If not specified, create a new instance.
        instance_ip (str): IP or URL address of an already existing CSP instance to use.
            If not specified, create a new instance.
        stop_mode (str or int): Define the "stop" method behavior.
            Default to 'term' if new instance, or 'keep' if already existing instance.
            See "stop_mode" property for more information and possible values.
        exit_instance_on_signal (bool): If True, exit instance
            on OS exit signals. This may help to not have instance still running
            if Python interpreter is not exited properly. Note: this is provided for
            convenience and does not cover all exit case like process kill and
            may not work on all OS.
    """
    #: CSP provider name (str), must be the same as expected "provider" argument value
    NAME = None

    #: Link to CSP documentation or website
    DOC_URL = ''

    #: Timeout for instance status change in seconds
    TIMEOUT = 360.0

    #: Possible stop_mode int values
    STOP_MODES = {
        0: "term",
        1: "stop",
        2: "keep"}

    #: Instance status when running
    STATUS_RUNNING = 'running'

    #: Instance status when stopped
    STATUS_STOPPED = 'stopped'

    # Attributes returned as dict by "info" property
    _INFO_NAMES = {
        '_provider', 'public_ip', 'private_ip',
        '_region', '_instance_type', '_ssh_key', '_security_group', '_instance_id',
        '_stop_mode', '_url', '_instance_type_name'}

    def __new__(cls, **kwargs):
        # If call from a subclass, instantiate this subclass directly
        if cls is not CSPGenericClass:
            return object.__new__(cls)

        # Get provider from configuration or argument
        config = _cfg.create_configuration(kwargs.get('config'))
        provider = cls._provider_from_config(kwargs.get('provider'), config)

        # Finds module containing CSP class
        module_name = '%s.%s' % (cls.__module__, provider.lower())
        try:
            csp_module = _import_module(module_name)
        except ImportError as exception:
            if provider.lower() in str(exception):
                # If ImportError for current module name, may be
                # a configuration error.
                raise _exc.CSPConfigurationException(
                    "No module '%s' for '%s' provider" % (module_name, provider))
            # ImportError of another module, raised as it
            raise

        # Finds CSP class
        for name in dir(csp_module):
            member = getattr(csp_module, name)
            try:
                if getattr(member, 'NAME') == provider:
                    break
            except AttributeError:
                continue
        else:
            raise _exc.CSPConfigurationException(
                "No class found in '%s' for '%s' provider" % (module_name, provider))

        # Instantiates CSP class
        return object.__new__(member)

    def __init__(self, provider=None, config=None, client_id=None, secret_id=None, region=None,
                 instance_type=None, ssh_key=None, security_group=None, instance_id=None,
                 instance_ip=None,
                 stop_mode=None, exit_instance_on_signal=False, **kwargs):

        # Default some attributes
        self._session = None
        self._instance = None
        self._config_env = {}
        self._image_id = None
        self._image_name = None
        self._instance_type = None
        self._instance_type_name = None
        self._accelerator = None
        self._stop_mode = None

        # Read configuration from file
        config = _cfg.create_configuration(config)

        self._provider = self._provider_from_config(provider, config)

        self._client_id = config.get_default(
            'csp', 'client_id', overwrite=client_id)
        self._secret_id = config.get_default(
            'csp', 'secret_id', overwrite=secret_id)
        self._region = config.get_default(
            'csp', 'region', overwrite=region)
        self._instance_type = config.get_default(
            'csp', 'instance_type', overwrite=instance_type)
        self._ssh_key = config.get_default(
            'csp', 'ssh_key', overwrite=ssh_key,
            default=self._default_parameter_value(
                'KeyPair', include_provider=True))
        self._security_group = config.get_default(
            'csp', 'security_group', overwrite=security_group,
            default=self._default_parameter_value('SecurityGroup'))
        self._instance_id = config.get_default(
            'csp', 'instance_id', overwrite=instance_id)
        self._url = _utl.format_url(config.get_default(
            'csp', 'instance_ip', overwrite=instance_ip))
        self.stop_mode = config.get_default(
            "csp", "stop_mode", overwrite=stop_mode,
            default='keep' if instance_id or instance_ip else 'term')

        # Checks mandatory configuration values
        self._check_arguments('region')

        if (self._client_id is None and
                self._instance_id is None and
                self._url is None):
            raise _exc.CSPConfigurationException(
                "Need at least 'client_id', 'instance_id' or 'instance_ip' "
                "argument. See documentation for more information.")

        # Enable optional Signal handler
        self._set_signals(exit_instance_on_signal)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.stop()

    def __del__(self):
        self.stop()

    @property
    def provider(self):
        """
        Cloud Service Provider

        Returns:
            str: CSP name
        """
        return self._provider

    @property
    def public_ip(self):
        """
        Public IP of the current instance.

        Returns:
            str: IP address

        Raises:
            acceleratorAPI.exceptions.CSPInstanceException:
                No instance from which get IP.
        """
        if self._instance is None:
            raise _exc.CSPInstanceException("No instance found")
        return self._get_public_ip()

    @_abstractmethod
    def _get_public_ip(self):
        """
        Read current instance public IP from CSP instance.

        Returns:
            str: IP address
        """

    @property
    def private_ip(self):
        """
        Private IP of the current instance.

        Returns:
            str: IP address

        Raises:
            acceleratorAPI.exceptions.CSPInstanceException:
                No instance from which get IP.
        """
        if self._instance is None:
            raise _exc.CSPInstanceException("No instance found")
        return self._get_private_ip()

    @_abstractmethod
    def _get_private_ip(self):
        """
        Read current instance private IP from CSP instance.

        Returns:
            str: IP address
        """

    @property
    def url(self):
        """
        URL of the current instance.

        Returns:
            str: URL
        """
        # Check if status OK
        self._status()

        # Returns URL
        return self._url

    @property
    def instance_id(self):
        """
        ID of the current instance.

        Returns:
            str: ID
        """
        return self._instance_id

    @property
    def stop_mode(self):
        """
        Define the "stop" method behavior.

        Possible values ares:
            0: TERM, terminate and delete instance.
            1: STOP, stop and pause instance.
            2: KEEP, let instance running.

        "stop" can be called manually but is also called when:
            - "with" exit if class is used as context manager.
            - On CSP object deletion by garbage collector.
            - On OS signals if "exit_instance_on_signal" was set to True
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

    @_abstractmethod
    def _check_credential(self):
        """
        Check CSP credentials.

        Raises:
            acceleratorAPI.exceptions.CSPAuthenticationException:
                Authentication failed.
        """

    def _status(self):
        """
        Returns current status of current instance.

        Returns:
            str: Status

        Raises:
            acceleratorAPI.exceptions.CSPInstanceException:
                No instance from which get status.
        """
        if self._instance_id is None:
            raise _exc.CSPInstanceException("No instance ID provided")

        # Update instance
        self._instance = self._get_instance()

        if self._instance is None:
            raise _exc.CSPInstanceException("No instance available")

        # Read instance status
        return self._get_status()

    @_abstractmethod
    def _get_status(self):
        """
        Returns current status of current instance.

        Returns:
            str: Status
        """

    @_abstractmethod
    def _get_instance(self):
        """
        Returns current instance.

        Returns:
            object: Instance
        """

    @_abstractmethod
    def _init_key_pair(self):
        """
        Initialize key pair.

        Returns:
            bool: True if reuses existing key
        """

    def start(self, accel_client=None, accel_parameters=None, stop_mode=None):
        """
        Start instance if not already started. Create instance if necessary.

        Needs "accel_client" or "accel_parameters".

        Args:
            accel_client (acceleratorAPI.client.AcceleratorClient): Accelerator client.
            accel_parameters (dict): Can override parameters from accelerator client.
            stop_mode (str or int): See "stop_mode" property for more information.
        """
        # Updates stop mode
        self.stop_mode = stop_mode

        # Starts instance only if not already started
        if self._url is None:

            # Checks CSP credential
            self._check_credential()

            # Creates and starts instance if not exists
            if self.instance_id is None:

                # Get parameters from accelerator
                self._set_accelerator_requirements(
                    accel_client, accel_parameters)

                # Configure and create instance
                reuse_key = self._init_key_pair()
                _get_logger().info(
                    "Reused KeyPair %s" if reuse_key
                    else "Created KeyPair %s", self._ssh_key)

                try:
                    self._create_instance()
                except _exc.CSPException as exception:
                    self._stop_silently(exception)
                    raise

                try:
                    self._instance, self._instance_id = self._start_new_instance()
                except _exc.CSPException as exception:
                    self._stop_silently(exception)
                    raise

                _get_logger().info("Created instance ID: %s", self._instance_id)

            # If exists, starts it directly
            else:
                state = self._status()
                self._start_existing_instance(state)

            # Waiting for instance provisioning
            _get_logger().info("Waiting for the instance provisioning...")
            try:
                self._wait_instance_ready()
            except _exc.CSPException as exception:
                self._stop_silently(exception)
                raise

            # Update instance URL
            self._url = _utl.format_url(self.public_ip)

            # Waiting for the instance to boot
            _get_logger().info("Waiting for the instance booting...")
            self._wait_instance_boot()

        # If started from URl, checks this URL is reachable
        elif not _utl.check_url(self._url):
            raise _exc.CSPInstanceException("Unable to reach instance URL.")

        _get_logger().info("The instance is now up and running")

    @_abstractmethod
    def _create_instance(self):
        """
        Initialize and create instance.
        """

    @_abstractmethod
    def _start_new_instance(self):
        """
        Start a new instance.

        Returns:
            object: Instance
            str: Instance ID
        """

    @_abstractmethod
    def _start_existing_instance(self, status):
        """
        Start a existing instance.

        Args:
            status (str): Status of the instance.
        """

    def _wait_instance_ready(self):
        """
        Wait until instance is ready.
        """
        # Waiting for the instance provisioning
        with _utl.Timeout(self.TIMEOUT) as timeout:
            while True:
                # Get instance status
                status = self._status()
                if status.lower() == self.STATUS_RUNNING:
                    return
                elif timeout.reached():
                    raise _exc.CSPInstanceException(
                        "Timed out while waiting CSP instance provisioning"
                        " (last status: %s)." % status)

    def _wait_instance_boot(self):
        """Wait until instance has booted and webservice is OK

        Raises:
            acceleratorAPI.exceptions.CSPInstanceException:
                Timeout while booting."""
        if not _utl.check_url(self._url, timeout=self.TIMEOUT):
            raise _exc.CSPInstanceException("Timed out while waiting CSP instance to boot.")

    def _get_instance_name(self):
        """Returns name to use for instance name

        Returns:
            str: name"""
        return "Accelize accelerator %s" % self._accelerator

    @property
    def info(self):
        """
        Returns some instance information.

        Returns:
            dict: Dictionary containing information on
                current instance.
        """
        info = {}
        for name in self._INFO_NAMES:
            try:
                value = getattr(self, name)
            except (AttributeError, _exc.CSPException):
                continue
            info[name.strip('_')] = value
        return info

    def stop(self, stop_mode=None):
        """
        Stop instance accordingly with the current stop_mode.
        See "stop_mode" property for more information.

        Args:
            stop_mode (str or int): If not None, override current "stop_mode" value.
        """
        # No instance to stop
        if self._instance is None:
            return

        # Define stop mode
        if stop_mode is None:
            stop_mode = self._stop_mode

        # Keep instance alive
        if stop_mode == 'keep':
            import warnings
            warnings.warn("Instance with URL %s (ID=%s) is still running!" %
                          (self.url, self.instance_id),
                          Warning)
            return

        # Checks if instance to stop
        try:
            self._status()
        except _exc.CSPInstanceException:
            return

        # Terminates and delete instance completely
        if stop_mode == 'term':
            self._terminate_instance()
            self._instance = None
            _get_logger().info("Instance ID %s has been terminated", self._instance_id)

        # Pauses instance and keep it alive
        else:
            self._pause_instance()
            self._instance = None
            _get_logger().info("Instance ID %s has been stopped", self._instance_id)

    @_abstractmethod
    def _terminate_instance(self):
        """
        Terminates and deletes instance.
        """

    @_abstractmethod
    def _pause_instance(self):
        """
        Pauses instance.
        """

    def _stop_silently(self, exception):
        """
        Terminates and deletes instance ignoring errors.

        Args:
            exception(Exception): If provided, augment message
                of this exception with CSP help.
        """
        # Augment exception message
        if exception is not None:
            self._add_csp_help_to_exception_message(exception)

        # Force stop instance, ignore exception if any
        try:
            self._terminate_instance()
        except _exc.CSPException:
            pass

    def _set_accelerator_requirements(self, accel_client=None, accel_parameters=None):
        """
        Configures instance with accelerator client parameters.

        Needs "accel_client" or "accel_parameters".

        Args:
            accel_client (acceleratorAPI.client.AcceleratorClient): Accelerator client.
            accel_parameters (dict): Can override parameters from accelerator client.

        Raises:
            acceleratorAPI.exceptions.CSPConfigurationException:
                Parameters are not valid..
        """
        # Get parameters
        parameters = dict()
        if accel_client is not None:
            parameters.update(accel_client.get_requirements(self._provider))

        if accel_parameters is not None:
            parameters.update(accel_parameters)

        # Check if region is valid
        if self._region not in parameters.keys():
            raise _exc.CSPConfigurationException(
                "Region '%s' is not supported. Available regions are: %s", self._region,
                ', '.join(parameters))

        # Get accelerator name
        self._accelerator = parameters['accelerator']

        # Set parameters for current region
        region_parameters = parameters[self._region]
        self._image_id = self._get_image_id_from_region(region_parameters)
        self._instance_type = self._get_instance_type_from_region(region_parameters)
        self._config_env = self._get_config_env_from_region(region_parameters)

    def _get_image_id_from_region(self, accel_parameters_in_region):
        """
        Read accelerator parameters and get image id.

        Args:
            accel_parameters_in_region (dict): AcceleratorClient parameters
                for the current CSP region.

        Returns:
            str: image_id
        """
        return accel_parameters_in_region['image']

    def _get_instance_type_from_region(self, accel_parameters_in_region):
        """
        Read accelerator parameters and instance type.

        Args:
            accel_parameters_in_region (dict): AcceleratorClient parameters
                for the current CSP region.

        Returns:
            str: instance_type
        """
        return accel_parameters_in_region['instancetype']

    def _get_config_env_from_region(self, accel_parameters_in_region):
        """
        Read accelerator parameters and get configuration environment.

        Args:
            accel_parameters_in_region (dict): AcceleratorClient parameters
                for the current CSP region.

        Returns:
            dict: configuration environment
        """
        return self._config_env

    def get_configuration_env(self, **kwargs):
        """
        Return environment to pass to
        "acceleratorAPI.client.AcceleratorClient.start"
        "csp_env" argument.

        Args:
            kwargs:

        Returns:
            dict: Configuration environment.
        """
        return self._config_env

    @classmethod
    def _provider_from_config(cls, provider, config):
        """
        Get CSP provider from configuration.

        Args:
            provider (str): Override result if not None.
            config (acceleratorAPI.configuration.Configuration): Configuration.

        Returns:
            str: CSP provider.

        Raises:
            acceleratorAPI.exceptions.CSPConfigurationException: No provider found.
        """
        provider = config.get_default("csp", "provider", overwrite=provider)
        if not provider:
            # Use default value if any
            provider = cls.NAME
        if not provider:
            raise _exc.CSPConfigurationException("No CSP provider defined.")
        return provider

    def _set_signals(self, exit_instance_on_signal=True):
        """
        Set a list of interrupt signals to be handled asynchronously to emergency stop
        instance in case of unexpected exit.

        Args:
            exit_instance_on_signal (bool): If True, enable stop on signals.
        """
        if not exit_instance_on_signal:
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
            acceleratorAPI.exceptions.CSPConfigurationException:
                A specified argument is None.
        """
        for name in arg_name:
            if getattr(self, '_%s' % name) is None:
                raise _exc.CSPConfigurationException(
                    "Parameter '%s' is required %s" % (name, self._provider))

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

    @classmethod
    def _default_parameter_value(cls, parameter_name, include_provider=False):
        """
        Returns a CamelCase name for default parameter
        value.

        Args:
            parameter_name (str): Name of parameter
            include_provider (bool): If True, include provider name in name.

        Returns:
            str: default parameter value.
        """
        return 'Accelize%s%s' % (cls.NAME if include_provider else '', parameter_name)
