import os

try:
    # Python 3
    from abc import ABC, abstractmethod
except ImportError:
    # Python 2
    from abc import ABCMeta, abstractmethod
    ABC = ABCMeta('ABC', (object,), {})

from acceleratorAPI import logger
import acceleratorAPI.utilities as _utl


class CSPException(Exception):
    """Generic CSP related exception"""


class CSPInstanceException(Exception):
    """Error with CSP instance"""


class CSPGenericClass(ABC):

    def __init__(self, provider, config, client_id=None, secret_id=None, region=None,
                 instance_type=None, ssh_key=None, security_group=None, instance_id=None,
                 instance_url=None):

        self._provider = provider

        # Read configuration from file
        self._config = config
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
    def check_csp_credential(self):
        """"""

    @abstractmethod
    def ssh_key_csp(self):
        """"""

    @abstractmethod
    def security_group_csp(self):
        """"""

    @abstractmethod
    def get_instance_csp(self):
        """"""

    @abstractmethod
    def set_accelerator_requirements(self, accel_parameters):
        """"""

    @abstractmethod
    def get_configuration_env(self, **kwargs):
        """"""

    @abstractmethod
    def create_instance_csp(self):
        """"""

    @abstractmethod
    def get_instance_url(self):
        """"""

    @abstractmethod
    def wait_instance_ready(self):
        """"""

    @abstractmethod
    def start_new_instance_csp(self):
        """"""

    @abstractmethod
    def is_instance_id_valid(self):
        """"""

    @abstractmethod
    def start_existing_instance_csp(self):
        """"""

    @abstractmethod
    def start_instance_csp(self):
        """"""

    @abstractmethod
    def stop_instance_csp(self, terminate=True):
        """"""

    @property
    def _ssh_dir(self):
        """
        SSH keys directory

        Returns:
            path (str)
        """
        if self._ssh_dir_cache is None:
            # Initialize value and check folder on first call
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
    def _get_from_args(key, **kwargs):
        return kwargs.pop(key, None)

    @staticmethod
    def get_host_public_ip():
        for url, section in (('http://ipinfo.io/ip', ''),
                             ('http://ip-api.com/xml', 'query'),
                             ('http://freegeoip.net/xml', 'IP')):

            try:
                # Try to get response
                logger.debug("Get public IP answer using: %s", url)
                session = _utl.https_session(max_retries=1)
                response = session.get(url)
                response.raise_for_status()

                # Parse IP from response
                if section:
                    try:
                        # Use lxml if available
                        import lxml.etree as ET
                    except ImportError:
                        import xml.etree.ElementTree as ET

                    root = ET.fromstring(response.text.encode('utf-8'))
                    ip_address = str(root.findall(section)[0].text)
                else:
                    ip_address = str(response.text)

                logger.debug("Public IP answer: %s", ip_address)
                return "/32%s" % ip_address.strip()
            except Exception:
                logger.exception("Caught following exception:")

        logger.error("Failed to find your external IP address after attempts to 3 different sites.")
        raise Exception("Failed to find your external IP address. Your internet connection might be broken.")


class CSPClassFactory(object):

    def __new__(cls, config, provider=None, **kwargs):

        if provider is None:
            try:
                provider = config.get("csp", "provider")
            except Exception:
                raise Exception("Could not find a 'provider' key in the 'csp' section.")
        logger.info("Targeted CSP: %s.", provider)

        if provider == 'AWS':
            from acceleratorAPI.csp.aws import AWSClass
            return AWSClass(provider, config, **kwargs)
        elif provider == 'OVH':
            from acceleratorAPI.csp.ovh import OVHClass
            return OVHClass(provider, config, **kwargs)
        else:
            raise ValueError('Cannot instantiate a CSP class with this provider:' + str(provider))
