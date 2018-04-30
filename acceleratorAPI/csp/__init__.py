import os

try:
    # Python 3
    from abc import ABC, abstractmethod
except ImportError:
    # Python 2
    from abc import ABCMeta, abstractmethod
    ABC = ABCMeta('ABC', (object,), {})

import requests
from requests.adapters import HTTPAdapter

from acceleratorAPI import logger


class CSPGenericClass(ABC):

    def __init__(self, config_parser, client_id=None, secret_id=None, region=None,
                 instance_type=None, ssh_key=None, security_group=None, instance_id=None,
                 instance_url=None):
        self.config_parser = config_parser
        self.client_id = self._get_from_config('csp', 'client_id', overwrite=client_id)
        self.secret_id = self._get_from_config('csp', 'secret_id', overwrite=secret_id)
        self.region = self._get_from_config('csp', 'region', overwrite=region)
        self.instance_type = self._get_from_config('csp', 'instance_type', overwrite=instance_type)
        self.ssh_key = self._get_from_config('csp', 'ssh_key', overwrite=ssh_key, default="MySSHKey")
        self.security_group = self._get_from_config('csp', 'security_group', overwrite=security_group,
                                                    default="MySecurityGroup")
        self.instance_id = self._get_from_config('csp', 'instance_id', overwrite=instance_id)
        self.instance_url = self._get_from_config('csp', 'instance_url', overwrite=instance_url)

        self.ssh_dir = os.path.expanduser('~/.ssh')
        self.create_SSH_folder()  # If not existing create SSH folder in HOME folder

    def __str__(self):
        return ', '.join("%s:%s" % item for item in vars(self).items())

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
    def is_instance_ID_valid(self):
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

    def create_SSH_folder(self):
        try:
            os.mkdir(self.ssh_dir, 0o700)
        except OSError:
            pass

    def create_SSH_key_filename(self):
        ssh_key_file = "%s.pem" % self.ssh_key
        ssh_files = os.listdir(self.ssh_dir)
        if ssh_key_file not in ssh_files:
            return os.path.join(self.ssh_dir, ssh_key_file)
        idx = 1
        while True:
            ssh_key_file = "%s_%d.pem" % (self.ssh_key, idx)
            if ssh_key_file not in ssh_files:
                break
            idx += 1
        logger.warning(
            ("A SSH key file named '%s' is already existing in ~/.ssh. "
             "To avoid overwriting an existing key, the new SSH key file will be named '%s'."),
            self.ssh_key, ssh_key_file)
        return os.path.join(self.ssh_dir, ssh_key_file)

    def _get_from_config(self, section, key, overwrite=None, default=None):
        return self.config_parser.get_default(section, key, overwrite, default)

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
                session = requests.Session()
                session.mount(url, HTTPAdapter(max_retries=1))
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

    def __new__(cls, config_parser, provider=None, **kwargs):

        if provider is None:
            try:
                provider = config_parser.get("csp", "provider")
            except Exception:
                raise Exception("Could not find a 'provider' key in the 'csp' section.")
        logger.info("Targeted CSP: %s.", provider)
        if provider.lower() == 'aws':
            from acceleratorAPI.csp.aws import AWSClass
            return AWSClass(provider, config_parser, **kwargs)
        elif provider.lower() == 'ovh':
            from acceleratorAPI.csp.ovh import OVHClass
            return OVHClass(provider, config_parser, **kwargs)
        else:
            raise ValueError('Cannot initate a CSP class with this provider:' + str(provider))
