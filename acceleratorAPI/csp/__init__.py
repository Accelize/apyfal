# coding=utf-8
import os

try:
    # Python 3
    from abc import ABC, abstractmethod
except ImportError:
    # Python 2
    from abc import ABCMeta, abstractmethod
    ABC = ABCMeta('ABC', (object,), {})

from acceleratorAPI import logger, AccceleratorApiBaseException as _AccceleratorApiBaseException
import acceleratorAPI.configuration as _cfg


class CSPException(_AccceleratorApiBaseException):
    """Generic CSP related exception"""


class CSPInstanceException(CSPException):
    """Error with CSP instance"""


class CSPAuthenticationException(CSPException):
    """Error while trying to authenticate user."""


class CSPConfigurationException(CSPException):
    """Error with CSP configuration"""


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
    """

    def __new__(cls, provider, config, **kwargs):
        # If call from a subclass, instantiate this subclass directly
        if cls is not CSPGenericClass:
            return ABC.__new__(cls)

        # If call form this class instantiate subclasses depending on Provider
        config = _cfg.create_configuration(config)
        provider = cls._provider_from_config(provider, config)
        logger.info("Targeted CSP: %s.", provider)

        if provider == 'AWS':
            from acceleratorAPI.csp.aws import AWSClass
            return ABC.__new__(AWSClass)

        elif provider == 'OVH':
            from acceleratorAPI.csp.ovh import OVHClass
            return ABC.__new__(OVHClass)

        else:
            raise CSPConfigurationException(
                "Cannot instantiate a CSP class with this '%s' provider" % provider)

    def __init__(self, provider, config, client_id=None, secret_id=None, region=None,
                 instance_type=None, ssh_key=None, security_group=None, instance_id=None,
                 instance_url=None):

        # Read configuration from file
        self._config = _cfg.create_configuration(config)
        self._provider = self._provider_from_config(provider, config)
        self._get_from_config = config.get_default

        self._client_id = self._get_from_config('csp', 'client_id', overwrite=client_id)
        self._secret_id = self._get_from_config('csp', 'secret_id', overwrite=secret_id)
        self._region = self._get_from_config('csp', 'region', overwrite=region)
        self._instance_type = self._get_from_config('csp', 'instance_type', overwrite=instance_type)
        self._ssh_key = self._get_from_config('csp', 'ssh_key', overwrite=ssh_key, default="MySSHKey")
        self._security_group = self._get_from_config('csp', 'security_group', overwrite=security_group,
                                                     default="MySecurityGroup")
        self._instance_id = self._get_from_config('csp', 'instance_id', overwrite=instance_id)
        self._instance_url = self._get_from_config('csp', 'instance_url', overwrite=instance_url)

        # Default some subclass required attributes
        self._instance = None
        self._config_env = {}
        self._image_id = None

        self._ssh_dir_cache = None

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
    def instance_id(self):
        return self._instance_id

    @abstractmethod
    def load_session(self):
        """"""

    @abstractmethod
    def check_credential(self):
        """"""

    @abstractmethod
    def ssh_key(self):
        """"""

    @abstractmethod
    def security_group(self):
        """"""

    @abstractmethod
    def get_instance_status(self):
        """"""

    @abstractmethod
    def set_accelerator_requirements(self, accel_parameters):
        """"""

    @abstractmethod
    def get_configuration_env(self, **kwargs):
        """"""

    @abstractmethod
    def create_instance(self):
        """"""

    @abstractmethod
    def get_instance_url(self):
        """"""

    @abstractmethod
    def wait_instance_ready(self):
        """"""

    @abstractmethod
    def start_new_instance(self):
        """"""

    @abstractmethod
    def is_instance_id_valid(self):
        """"""

    @abstractmethod
    def start_existing_instance(self):
        """"""

    @abstractmethod
    def start_instance(self):
        """"""

    @abstractmethod
    def stop_instance(self, terminate=True):
        """"""

    @property
    def _ssh_dir(self):
        """
        SSH keys directory

        Returns:
            path (str)
        """
        # Initialize value and check folder on first call
        if self._ssh_dir_cache is None:
            self._ssh_dir_cache = os.path.expanduser('~/.ssh')
            try:
                os.mkdir(self._ssh_dir_cache, 0o700)
            except OSError:
                pass

        return self._ssh_dir_cache

    def _create_ssh_key_filename(self):
        ssh_key_file = "%s.pem" % self._ssh_key
        ssh_files = os.listdir(self._ssh_dir)

        if ssh_key_file not in ssh_files:
            return os.path.join(self._ssh_dir, ssh_key_file)

        idx = 1
        while True:
            ssh_key_file = "%s_%d.pem" % (self._ssh_key, idx)
            if ssh_key_file not in ssh_files:
                break
            idx += 1

        logger.warning(
            ("A SSH key file named '%s' is already existing in ~/.ssh. "
             "To avoid overwriting an existing key, the new SSH key file will be named '%s'."),
            self._ssh_key, ssh_key_file)

        return os.path.join(self._ssh_dir, ssh_key_file)

    @staticmethod
    def _provider_from_config(provider, config):
        provider = config.get_default("csp", "provider", overwrite=provider)
        if provider is None:
            raise CSPConfigurationException("No CSP provider defined.")
        return provider
