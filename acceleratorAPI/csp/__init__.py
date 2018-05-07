# coding=utf-8
"""Cloud Service Providers"""

try:
    # Python 3
    from abc import ABC, abstractmethod
except ImportError:
    # Python 2
    from abc import ABCMeta, abstractmethod
    ABC = ABCMeta('ABC', (object,), {})

from acceleratorAPI import logger
import acceleratorAPI.configuration as _cfg
import acceleratorAPI.exceptions as _exc
import acceleratorAPI._utilities  as _utl


TERM = 0
STOP = 1
KEEP = 2


class CSPGenericClass(ABC):
    """This is base abstract class for all CSP classes.

    This is also a factory which instantiate CSP subclass related to
    specified Cloud Service Provider.

    Args:
        provider (str): Cloud service provider name.
        config (str or acceleratorAPI.configuration.Configuration): Configuration file path or instance
        client_id:
        secret_id:
        region:
        instance_type:
        ssh_key:
        security_group:
        instance_id:
        instance_url:
        project_id:
        auth_url:
        interface:
        role:
        exit_instance_on_signal (bool): If True, exit CSP instances
            on OS exit signals. This may help to not have instance still running
            if accelerator is not exited properly. Note: this is provided for
            convenience and does not cover all exit case like process kill and
            may not work on every OS.
    """
    STOP_MODES = {
        TERM: "TERM",
        STOP: "STOP",
        KEEP: "KEEP"}

    def __new__(cls, **kwargs):
        # If call from a subclass, instantiate this subclass directly
        if cls is not CSPGenericClass:
            return ABC.__new__(cls)

        # If call form this class instantiate subclasses depending on Provider
        config = _cfg.create_configuration(kwargs.get('config'))
        provider = cls._provider_from_config(kwargs.get('provider'), config)
        logger.info("Targeted CSP: %s.", provider)

        if provider == 'AWS':
            from acceleratorAPI.csp.aws import AWSClass
            return ABC.__new__(AWSClass)

        elif provider == 'OVH':
            from acceleratorAPI.csp.ovh import OVHClass
            return ABC.__new__(OVHClass)

        else:
            raise _exc.CSPConfigurationException(
                "Cannot instantiate a CSP class with this '%s' provider" % provider)

    def __init__(self, provider=None, config=None, client_id=None, secret_id=None, region=None,
                 instance_type=None, ssh_key=None, security_group=None, instance_id=None,
                 instance_url=None, project_id=None, auth_url=None, interface=None, role=None,
                 exit_instance_on_signal=True, stop_mode=None):

        # Read configuration from file
        self._config = _cfg.create_configuration(config)
        self._provider = self._provider_from_config(provider, config)

        self._client_id = config.get_default('csp', 'client_id', overwrite=client_id)
        self._secret_id = config.get_default('csp', 'secret_id', overwrite=secret_id)
        self._region = config.get_default('csp', 'region', overwrite=region)
        self._instance_type = config.get_default('csp', 'instance_type', overwrite=instance_type)
        self._ssh_key = config.get_default('csp', 'ssh_key', overwrite=ssh_key, default="MySSHKey")
        self._security_group = config.get_default('csp', 'security_group', overwrite=security_group,
                                                  default="MySecurityGroup")
        self._instance_id = config.get_default('csp', 'instance_id', overwrite=instance_id)
        self._instance_url = config.get_default(
            'csp', 'instance_url', overwrite=_utl.format_url(instance_url))

        self._role = config.get_default('csp', 'role', overwrite=role)

        self._project_id = config.get_default('csp', 'project_id', overwrite=project_id)
        self._auth_url = config.get_default('csp', 'auth_url', overwrite=auth_url)
        self._interface = config.get_default('csp', 'interface', overwrite=interface)

        self._stop_mode = int(config.get_default("csp", "stop_mode", overwrite=stop_mode, default=TERM))

        # Default some subclass required attributes
        self._session = None
        self._instance = None
        self._config_env = {}
        self._image_id = None
        self._accelerator = None

        self._ssh_dir_cache = None

        # Enable optional Signal handler
        if exit_instance_on_signal:
            self._set_signals()

    def __str__(self):
        return ', '.join("%s:%s" % item for item in vars(self).items())

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.stop_instance()

    def __del__(self):
        self.stop_instance()

    @property
    def provider(self):
        return self._provider

    @property
    def instance_url(self):
        return self._instance_url

    @property
    def instance_ip(self):
        if self._instance is None:
            raise _exc.CSPInstanceException("No instance found")
        return self._get_instance_public_ip()

    @property
    def instance_id(self):
        return self._instance_id

    @property
    def stop_mode(self):
        """
        Stop mode

        Returns:
            int: stop mode
        """
        return self._stop_mode

    @stop_mode.setter
    def stop_mode(self, stop_mode):
        if stop_mode is None:
            return

        try:
            stop_mode = int(stop_mode)
        except TypeError:
            pass

        if stop_mode not in self.STOP_MODES:
            raise ValueError(
                "Invalid value %s, Possible values are %s" % (
                    stop_mode, ', '.join("%s: %d" % (name, value)
                                         for value, name in self.STOP_MODES.items())))

        self._stop_mode = stop_mode
        logger.info("Auto-stop mode is: %s", self.STOP_MODES[self._stop_mode])

    @abstractmethod
    def check_credential(self):
        """"""

    @abstractmethod
    def security_group(self):
        """"""

    def get_instance_status(self):
        """"""
        if self._instance_id is None:
            raise _exc.CSPInstanceException("No instance ID provided")
        return self._get_instance_status()

    @abstractmethod
    def set_accelerator_requirements(self, accel_parameters):
        """"""

    @abstractmethod
    def get_configuration_env(self, **kwargs):
        """"""

    def is_instance_id_valid(self):
        try:
            self.get_instance_status()
        except _exc.CSPInstanceException:
            logger.error("Could not find a instance with ID '%s' (%s)",
                         self._instance_id)
            return False
        logger.info("Using instance ID: %s", self._instance_id)
        return True

    def stop_instance(self, stop_mode=None):
        """"""
        if stop_mode is None:
            stop_mode = self._stop_mode

        # Keep instance alive
        if self._stop_mode == KEEP:
            logger.warning("###########################################################")
            logger.warning("## Instance with URL %s (ID=%s) is still running!",
                           self.instance_url, self.instance_id)
            logger.warning("## Make sure you will stop manually the instance.")
            logger.warning("###########################################################")
            return

        # Checks if instance to stop
        try:
            self.get_instance_status()
        except _exc.CSPInstanceException as exception:
            logger.debug("No instance to stop (%s)", exception)
            return

        logger.debug("Stopping instance (ID: %s) on '%s'", self.instance_id, self.provider)

        # Terminates and delete instance completely
        if stop_mode == TERM:
            response = self._terminate_instance()
            logger.info("Instance ID %s has been terminated", self._instance_id)

        # Pauses instance and keep it alive
        else:
            response = self._pause_instance()
            logger.info("Instance ID %s has been stopped", self._instance_id)

        if response is not None:
            logger.debug("Stop response: %s", response)

    def start_instance(self):
        # Starts instance only if not already started
        if self.instance_url is None:

            # Checks CSP credential
            self.check_credential()

            # Creates and starts instance if not exists
            if self.instance_id is None:
                self._create_instance()

                logger.debug("Starting instance")
                self._instance, self._instance_id = self._start_new_instance()
                logger.info("Created instance ID: %s", self._instance_id)

            # If exists, starts it directly
            else:
                state = self.get_instance_status()
                self._start_existing_instance(state)

            # Waiting for instance provisioning
            self._wait_instance_ready()

            # Waiting for the instance to boot
            self._wait_instance_boot()

        self._log_instance_info()
        logger.info("Your instance is now up and running")

    @abstractmethod
    def _init_ssh_key(self):
        """"""
    @abstractmethod
    def _create_instance(self):
        """"""

    @abstractmethod
    def _get_instance_public_ip(self):
        """"""

    @abstractmethod
    def _get_instance_status(self):
        """"""

    @abstractmethod
    def _start_new_instance(self):
        """"""

    @abstractmethod
    def _start_existing_instance(self):
        """"""

    @abstractmethod
    def _log_instance_info(self):
        """"""

    @abstractmethod
    def _terminate_instance(self):
        """"""

    @abstractmethod
    def _pause_instance(self):
        """"""

    @abstractmethod
    def _wait_instance_ready(self):
        """"""

    def _update_instance_url(self):
        self._instance_url = _utl.format_url(self.instance_ip)

    def _get_region_parameters(self, accel_parameters):
        # Check if region is valid
        if self._region not in accel_parameters.keys():
            raise _exc.CSPConfigurationException(
                "Region '%s' is not supported. Available regions are: %s", self._region,
                ', '.join(accel_parameters))

        # Get accelerator name
        self._accelerator = accel_parameters['accelerator']

        # Get parameters for current region
        return accel_parameters[self._region]

    def _wait_instance_boot(self):
        logger.info("Instance is now booting...")

        # Check URL with 6 minutes timeout
        self._update_instance_url()
        if not _utl.check_url(self._instance_url, timeout=1,
                              retry_count=72, logger=logger):
            raise _exc.CSPInstanceException("Timed out while waiting CSP instance to boot.")

        logger.info("Instance booted!")

    @staticmethod
    def _provider_from_config(provider, config):
        provider = config.get_default("csp", "provider", overwrite=provider)
        if provider is None:
            raise _exc.CSPConfigurationException("No CSP provider defined.")
        return provider

    def _set_signals(self):
        """
        Set a list of interrupt signals to be handled asynchronously to emergency stop
        instance in case of unexpected exit.
        """
        # Lazy import since optional feature
        import signal

        for signal_name in ('SIGTERM', 'SIGINT', 'SIGQUIT'):
            # Check signal exist on current OS before setting it
            if hasattr(signal, signal_name):
                signal.signal(getattr(signal, signal_name), self.stop_instance)
