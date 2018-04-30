import os

try:
    # Python 3
    from configparser import ConfigParser
except ImportError:
    # Python 2
    from ConfigParser import ConfigParser

import requests
from requests.adapters import HTTPAdapter

from acceleratorAPI import logger


# ===================================
class CSPGenericClass(object):
    # ===================================
    @staticmethod
    def get_from_args(key, **kwargs):
        return kwargs.pop(key, None)

    @staticmethod
    def get_host_public_ip_case1():
        try:
            url = 'http://ipinfo.io/ip'
            logger.debug("Get public IP answer using: %s", url)
            s = requests.Session()
            s.mount(url, HTTPAdapter(max_retries=1))
            r = s.get(url)
            r.raise_for_status()
            ip_address = str(r.text)
            logger.debug("Public IP answer: %s", ip_address)
            return ip_address.strip() + "/32"
        except Exception:
            logger.exception("Caught following exception:")
            return None

    @staticmethod
    def get_host_public_ip_case2():
        try:
            import xml.etree.ElementTree as ET
            url = 'http://ip-api.com/xml'
            logger.debug("Get public IP answer using: %s", url)
            s = requests.Session()
            s.mount(url, HTTPAdapter(max_retries=1))
            r = s.get(url)
            r.raise_for_status()
            root = ET.fromstring(r.text.encode('utf-8'))
            ip_address = str(root.findall("query")[0].text)
            logger.debug("Public IP answer: %s", ip_address)
            return ip_address.strip() + "/32"
        except Exception:
            logger.exception("Caught following exception:")
            return None

    @staticmethod
    def get_host_public_ip_case3():
        try:
            import xml.etree.ElementTree as ET
            url = 'http://freegeoip.net/xml'
            logger.debug("Get public IP answer using: %s", url)
            s = requests.Session()
            s.mount(url, HTTPAdapter(max_retries=1))
            r = s.get(url)
            r.raise_for_status()
            root = ET.fromstring(r.text.encode('utf-8'))
            ip_address = str(root.findall("IP")[0].text)
            logger.debug("Public IP answer: %s", ip_address)
            return ip_address.strip() + "/32"
        except Exception:
            logger.exception("Caught following exception:")
            return None

    @staticmethod
    def get_host_public_ip():
        ip_address = CSPGenericClass.get_host_public_ip_case1()
        if ip_address:
            return ip_address
        ip_address = CSPGenericClass.get_host_public_ip_case2()
        if ip_address:
            return ip_address
        ip_address = CSPGenericClass.get_host_public_ip_case3()
        if ip_address:
            return ip_address
        logger.error("Failed to find your external IP address after attempts to 3 different sites.")
        raise Exception("Failed to find your external IP address. Your internet connection might be broken.")

    def __init__(self, config_parser, client_id=None, secret_id=None, region=None,
                 instance_type=None, ssh_key=None, security_group=None, instance_id=None,
                 instance_url=None):
        self.config_parser = config_parser
        self.client_id = self.get_from_config('csp', 'client_id', overwrite=client_id)
        self.secret_id = self.get_from_config('csp', 'secret_id', overwrite=secret_id)
        self.region = self.get_from_config('csp', 'region', overwrite=region)
        self.instance_type = self.get_from_config('csp', 'instance_type', overwrite=instance_type)
        self.ssh_key = self.get_from_config('csp', 'ssh_key', overwrite=ssh_key, default="MySSHKey")
        self.security_group = self.get_from_config('csp', 'security_group', overwrite=security_group,
                                                   default="MySecurityGroup")
        self.instance_id = self.get_from_config('csp', 'instance_id', overwrite=instance_id)
        self.instance_url = self.get_from_config('csp', 'instance_url', overwrite=instance_url)

        self.ssh_dir = os.path.expanduser('~/.ssh')
        self.create_SSH_folder()  # If not existing create SSH folder in HOME folder

    def create_SSH_folder(self):
        if not os.path.isdir(self.ssh_dir):
            os.mkdir(self.ssh_dir, 0o700)

    def create_SSH_key_filename(self):
        ssh_key_file = self.ssh_key + ".pem"
        ssh_files = os.listdir(self.ssh_dir)
        if ssh_key_file not in ssh_files:
            return os.path.join(self.ssh_dir, ssh_key_file)
        idx = 1
        while True:
            ssh_key_file = self.ssh_key + "_%d.pem" % idx
            if ssh_key_file not in ssh_files:
                break
            idx += 1
        logger.warn(
            ("A SSH key file named '%s' is already existing in ~/.ssh. "
             "To avoid overwriting an existing key, the new SSH key file will be named '%s'."),
            self.ssh_key, ssh_key_file)
        return os.path.join(self.ssh_dir, ssh_key_file)

    def get_from_config(self, section, key, overwrite=None, default=None):
        if overwrite is not None:
            return overwrite
        try:
            new_val = self.config_parser.get(section, key)
            if new_val:
                return new_val
            return default
        except Exception:
            return default


class CSPClassFactory(object):

    def __new__(cls, config_file, provider=None, **kwargs):
        config_parser = ConfigParser(allow_no_value=True)
        config_parser.read(config_file)
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
