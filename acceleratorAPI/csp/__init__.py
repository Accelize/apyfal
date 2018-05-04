# coding=utf-8
"""Cloud Service Providers"""

try:
    # Python 3
    from abc import ABC, abstractmethod
except ImportError:
    # Python 2
    from abc import ABCMeta, abstractmethod
    ABC = ABCMeta('ABC', (object,), {})

from acceleratorAPI import logger, AccceleratorApiBaseException as _AccceleratorApiBaseException
import acceleratorAPI.configuration as _cfg
import acceleratorAPI.utilities as _utl


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
        project_id:
        auth_url:
        interface:
        role:
    """

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
            raise CSPConfigurationException(
                "Cannot instantiate a CSP class with this '%s' provider" % provider)

    def __init__(self, provider=None, config=None, client_id=None, secret_id=None, region=None,
                 instance_type=None, ssh_key=None, security_group=None, instance_id=None,
                 instance_url=None, project_id=None, auth_url=None, interface=None, role=None):

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
        self._instance_url = config.get_default('csp', 'instance_url', overwrite=instance_url)

        self._role = config.get_default('csp', 'role', overwrite=role)

        self._project_id = config.get_default('csp', 'project_id', overwrite=project_id)
        self._auth_url = config.get_default('csp', 'auth_url', overwrite=auth_url)
        self._interface = config.get_default('csp', 'interface', overwrite=interface)

        # Default some subclass required attributes
        self._session = None
        self._instance = None
        self._config_env = {}
        self._image_id = None
        self._accelerator = None

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
    def check_credential(self):
        """"""

    @abstractmethod
    def _init_ssh_key(self):
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

    def _get_region_parameters(self, accel_parameters):
        # Check if region is valid
        if self._region not in accel_parameters.keys():
            raise CSPConfigurationException(
                "Region '%s' is not supported. Available regions are: %s", self._region,
                ', '.join(accel_parameters))

        # Get accelerator name
        self._accelerator = accel_parameters['accelerator']

        # Get parameters for current region
        return accel_parameters[self._region]

    def _wait_instance_boot(self):
        logger.info("Instance is now booting...")

        # Check URL with 6 minutes timeout
        self._instance_url = self.get_instance_url()
        if not _utl.check_url(self._instance_url, timeout=1,
                              retry_count=72, logger=logger):
            raise CSPInstanceException("Timed out while waiting CSP instance to boot.")

        logger.info("Instance booted!")

    @staticmethod
    def _provider_from_config(provider, config):
        provider = config.get_default("csp", "provider", overwrite=provider)
        if provider is None:
            raise CSPConfigurationException("No CSP provider defined.")
        return provider
