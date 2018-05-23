# coding=utf-8
"""Cloud Service Providers"""

from importlib import import_module as _import_module

try:
    # Python 3
    from abc import ABC as _ABC, abstractmethod as _abstractmethod
except ImportError:
    # Python 2
    from abc import ABCMeta as _ABCMeta, abstractmethod as _abstractmethod

    _ABC = _ABCMeta('ABC', (object,), {})

import acceleratorAPI.configuration as _cfg
import acceleratorAPI.exceptions as _exc
import acceleratorAPI._utilities as _utl
from acceleratorAPI._utilities import get_logger as _get_logger

TERM = 0
STOP = 1
KEEP = 2


class CSPGenericClass(_ABC):
    """This is base abstract class for all CSP classes.

    This is also a factory which instantiate CSP subclass related to
    specified Cloud Service Provider.

    Args:
        provider (str): Cloud service provider name.
            If set will override value from configuration file.
        config (str or acceleratorAPI.configuration.Configuration): Configuration file path or instance.
            If not set, will search it in current working directory, in current
            user "home" folder. If none found, will use default configuration values.
        client_id (str):CSP Client ID. See with your provider to generate this value.
            If set will override value from configuration file.
        secret_id (str):CSP secret ID. See with your provider to generate this value.
            If set will override value from configuration file.
        region (str): CSP region. Check with your provider which region are using instances with FPGA.
             If set will override value from configuration file.
        instance_type:
        ssh_key (str): SSH key to use with your CSP. If set will override value from configuration file.
        security_group:
        instance_id (str): CSP Instance ID to reuse. If set will override value from configuration file.
        instance_url (str): CSP Instance URL or IP address to reuse. If set will override value from configuration file.
        project_id:
        auth_url:
        interface:
        role:
        stop_mode (int): Define the "stop_instance" method behavior. See "stop_mode"
            property for more information and possible values.
        exit_instance_on_signal (bool): If True, exit CSP instances
            on OS exit signals. This may help to not have instance still running
            if Python interpreter is not exited properly. Note: this is provided for
            convenience and does not cover all exit case like process kill and
            may not work on all OS.
    """
    CSP_NAME = None
    CSP_HELP_URL = ''

    STOP_MODES = {
        TERM: "TERM",
        STOP: "STOP",
        KEEP: "KEEP"}

    _INFO_NAMES = {
        '_provider', 'instance_ip', 'instance_private_ip',
        '_region', '_instance_type', '_ssh_key', '_security_group', '_instance_id',
        '_role', '_project_id', '_auth_url', '_interface', '_stop_mode',
        '_instance_url', '_instance_type_name'}

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
        except ImportError:
            raise _exc.CSPConfigurationException(
                "No module '%s' for '%s' provider" % (module_name, provider))

        # Finds CSP class
        for name in dir(csp_module):
            member = getattr(csp_module, name)
            try:
                if getattr(member, 'CSP_NAME') == provider:
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
                 instance_url=None, project_id=None, auth_url=None, interface=None, role=None,
                 stop_mode=None, exit_instance_on_signal=False):

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
            'csp', 'ssh_key', overwrite=ssh_key, default="MySSHKey")
        self._security_group = config.get_default(
            'csp', 'security_group', overwrite=security_group, default="MySecurityGroup")
        self._instance_id = config.get_default(
            'csp', 'instance_id', overwrite=instance_id)
        self._instance_url = _utl.format_url(config.get_default(
            'csp', 'instance_url', overwrite=instance_url))
        self._role = config.get_default(
            'csp', 'role', overwrite=role)
        self._project_id = config.get_default(
            'csp', 'project_id', overwrite=project_id)
        self._auth_url = config.get_default(
            'csp', 'auth_url', overwrite=auth_url)
        self._interface = config.get_default(
            'csp', 'interface', overwrite=interface)
        self.stop_mode = config.get_default(
            "csp", "stop_mode", overwrite=stop_mode, default=TERM)

        # Checks mandatory configuration values
        self._check_arguments('region')

        # Enable optional Signal handler
        self._set_signals(exit_instance_on_signal)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.stop_instance()

    def __del__(self):
        self.stop_instance()

    @property
    def provider(self):
        """
        Cloud Service Provider

        Returns:
            str: CSP name
        """
        return self._provider

    @property
    def instance_ip(self):
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
        return self._get_instance_public_ip()

    @_abstractmethod
    def _get_instance_public_ip(self):
        """
        Read current instance public IP from CSP instance.

        Returns:
            str: IP address
        """

    @property
    def instance_private_ip(self):
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
        return self._get_instance_private_ip()

    @_abstractmethod
    def _get_instance_private_ip(self):
        """
        Read current instance private IP from CSP instance.

        Returns:
            str: IP address
        """

    @property
    def instance_url(self):
        """
        Public URL of the current instance.

        Returns:
            str: URL
        """
        return self._instance_url

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
        Define the "stop_instance" method behavior.

        Possible values ares:
            0: TERM, terminate and delete instance.
            1: STOP, stop and pause instance.
            2: KEEP, let instance running.

        "stop_instance" can be called manually but is also called when:
            - "with" exit if class is used as context manager.
            - On CSP object deletion by garbage collector.
            - On OS signals if "exit_instance_on_signal" was set to True
              on class instantiation.

        Returns:
            int: stop mode.
        """
        return self._stop_mode

    @stop_mode.setter
    def stop_mode(self, stop_mode):
        """
        Set stop_mode.

        Args:
            stop_mode (int): stop mode value to set
        """
        if stop_mode is None:
            return

        try:
            stop_mode = int(stop_mode)
        except (TypeError, ValueError):
            pass

        if stop_mode not in self.STOP_MODES:
            raise ValueError(
                "Invalid value %s, Possible values are %s" % (
                    stop_mode, ', '.join("%s: %d" % (name, value)
                                         for value, name in self.STOP_MODES.items())))

        self._stop_mode = stop_mode

    @_abstractmethod
    def check_credential(self):
        """
        Check CSP credentials.

        Raises:
            acceleratorAPI.exceptions.CSPAuthenticationException:
                Authentication failed.
        """

    def instance_status(self):
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
        return self._get_instance_status()

    @_abstractmethod
    def _get_instance_status(self):
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
    def _init_ssh_key(self):
        """
        Initialize SSH key.

        Returns:
            bool: True if reuses existing key
        """

    def start_instance(self):
        """
        Start instance if not already started. Create instance if necessary.
        """
        # Starts instance only if not already started
        if self.instance_url is None:

            # Checks CSP credential
            self.check_credential()

            # Creates and starts instance if not exists
            if self.instance_id is None:

                reuse_key = self._init_ssh_key()
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
                state = self.instance_status()
                self._start_existing_instance(state)

            # Waiting for instance provisioning
            _get_logger().info("Waiting for the instance provisioning...")
            try:
                self._wait_instance_ready()
            except _exc.CSPException as exception:
                self._stop_silently(exception)
                raise

            # Update instance URL
            self._instance_url = _utl.format_url(self.instance_ip)

            # Waiting for the instance to boot
            _get_logger().info("Waiting for the instance booting...")
            self._wait_instance_boot()

        # If started from URl, checks this URL is reachable
        elif not _utl.check_url(self._instance_url):
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
    def _start_existing_instance(self, state):
        """
        Start a existing instance.

        Args:
            state (str): Status of the instance.
        """

    @_abstractmethod
    def _wait_instance_ready(self):
        """
        Wait until instance is ready.
        """

    def _wait_instance_boot(self):
        """Wait until instance has booted and webservice is OK

        Raises:
            acceleratorAPI.exceptions.CSPInstanceException:
                Timeout while booting."""
        # Check URL with 6 minutes timeout
        if not _utl.check_url(self._instance_url, timeout=1, retry_count=72):
            raise _exc.CSPInstanceException("Timed out while waiting CSP instance to boot.")

    @property
    def instance_info(self):
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

    def stop_instance(self, stop_mode=None):
        """
        Stop instance accordingly with the current stop_mode.
        See "stop_mode" property for more information.

        Args:
            stop_mode (int): If not None, override current "stop_mode" value.
        """
        if stop_mode is None:
            stop_mode = self._stop_mode

        # Keep instance alive
        if stop_mode == KEEP:
            import warnings
            warnings.warn("Instance with URL %s (ID=%s) is still running!" %
                          (self.instance_url, self.instance_id),
                          Warning)
            return

        # Checks if instance to stop
        try:
            self.instance_status()
        except _exc.CSPInstanceException:
            return

        # Terminates and delete instance completely
        if stop_mode == TERM:
            self._terminate_instance()
            _get_logger().info("Instance ID %s has been terminated", self._instance_id)

        # Pauses instance and keep it alive
        else:
            self._pause_instance()
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

        # Force stop instance, hide exception if any
        try:
            self._terminate_instance()
        except _exc.CSPException:
            pass

    def set_accelerator_requirements(self, accel_parameters):
        """
        Configure instance with accelerator parameters.

        Args:
            accel_parameters (dict): Result from
                acceleratorAPI.accelerator.AcceleratorClient.get_requirements.

        Raises:
            acceleratorAPI.exceptions.CSPConfigurationException:
                Parameters are not valid..
        """
        # Check if region is valid
        if self._region not in accel_parameters.keys():
            raise _exc.CSPConfigurationException(
                "Region '%s' is not supported. Available regions are: %s", self._region,
                ', '.join(accel_parameters))

        # Get accelerator name
        self._accelerator = accel_parameters['accelerator']

        # Set parameters for current region
        region_parameters = accel_parameters[self._region]
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
        "acceleratorAPI.accelerator.AcceleratorClient.start"
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
            provider = cls.CSP_NAME
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
                signal.signal(getattr(signal, signal_name), self.stop_instance)

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
        if cls.CSP_HELP_URL:
            args = list(exception.args)
            try:
                args[0] += ', please refer to: %s' % cls.CSP_HELP_URL
            except TypeError:
                args[0] = 'CSP error, please refer to: %s' % cls.CSP_HELP_URL
            exception.args = tuple(args)
