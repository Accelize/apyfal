# coding=utf-8
"""Generic utilities used in acceleratorAPI code"""

import ast
import json
import os
import re
import time

import requests


_CACHE = dict()  # Store some cached values

# Constants
METERING_SERVER = 'https://master.metering.accelize.com'


def check_url(url, timeout=None, retry_count=0, retry_period=5):
    """
    Checking if an HTTP is up and running.

    Args:
        url (str): URL
        timeout (float): Timeout value in seconds.
        retry_count (int): Number of tries
        retry_period (float): Period between retries in seconds.

    Returns:
        bool: True if success, False elsewhere
    """
    if not url:
        return False

    miss_count = 0
    while miss_count <= retry_count:
        if miss_count and retry_period and retry_count:
            time.sleep(retry_period)
        try:
            status_code = requests.get(url, timeout=timeout).status_code
        except requests.RequestException:
            pass
        else:
            if status_code == 200:
                return True
        miss_count += 1

    return False


def format_url(url_or_ip):
    """
    Check format and format an IP address or URL to URL.
    If not directly an URL, format it to URL.

    Args:
        url_or_ip (str): URL or IP address.
            If None, skip check and return None.

    Returns:
        str: URL

    Raises:
        ValueError: Not a proper URL
    """
    # Skip if URL is None.
    if url_or_ip is None:
        return None

    # From "django.core.validator.URLValidator"
    url_validator = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  # ...or ipv4
        r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  # ...or ipv6
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    if re.match(url_validator, url_or_ip) is None:
        # Maybe only an IP, format it to URL and retry
        url = "http://%s" % url_or_ip
        if re.match(url_validator, url) is None:
            raise ValueError("Invalid URL '%s'" % url_or_ip)
        return url
    return url_or_ip


def http_session(max_retries=2):
    """
    Instantiate HTTP session

    Args:
        max_retries (int): The maximum number of retries each connection should attempt

    Returns:
        requests.Session: Http session
    """
    session = requests.Session()
    session.mount('http://', requests.adapters.HTTPAdapter(max_retries=max_retries))
    return session


def get_host_public_ip():
    """
    Find current host IP address.

    Returns:
        str: IP address

    Raises:
        OSError: Fail to get IP address
    """
    for url, section in (('http://ipinfo.io/ip', ''),
                         ('http://ip-api.com/xml', 'query'),
                         ('http://freegeoip.net/xml', 'IP')):

        # Try to get response
        session = http_session(max_retries=1)
        response = session.get(url)
        try:
            response.raise_for_status()
        except requests.exceptions.RequestException:
            continue

        # Parse IP from response
        if section:
            # XML parser lazy import since not always used
            try:
                # Use lxml if available
                import lxml.etree as ET
            except ImportError:
                # Else use standard library
                import xml.etree.ElementTree as ET

            root = ET.fromstring(response.text.encode('utf-8'))
            ip_address = str(root.findall(section)[0].text)
        else:
            ip_address = str(response.text)

        return "/32%s" % ip_address.strip()

    raise OSError("Failed to find your external IP address. Your internet connection might be broken.")


def pretty_dict(obj):
    """
    Format dictionary to text.

    Args:
        obj (dict): Dict to format.

    Returns:
        str: formatted dict
    """
    return json.dumps(ast.literal_eval(str(obj)), indent=4)


def create_ssh_key_file(ssh_key, key_content):
    """
    Create SSH key file.

    Args:
        ssh_key (str): key name
        key_content (str): key content
    """
    # Path to SSH keys dir
    ssh_dir = os.path.expanduser('~/.ssh')
    try:
        # Create if not exists
        os.mkdir(ssh_dir, 0o700)
    except OSError:
        if not os.path.isdir(os.path.dirname(ssh_dir)):
            raise

    # Find SSH key file path
    ssh_key_file = "%s.pem" % ssh_key
    ssh_files = os.listdir(ssh_dir)

    if ssh_key_file not in ssh_files:
        return os.path.join(ssh_dir, ssh_key_file)

    idx = 1
    while True:
        ssh_key_file = "%s_%d.pem" % (ssh_key, idx)
        if ssh_key_file not in ssh_files:
            break
        idx += 1

    key_filename = os.path.join(ssh_dir, ssh_key_file)

    # Create file
    with open(key_filename, "wt") as key_file:
        key_file.write(key_content)
    os.chmod(key_filename, 0o400)


def get_logger(stdout=False):
    """
    Initialize logger

    Args:
        stdout (bool): If True, configure logger to print on
            stdout, else use NullHandler

    Returns:
       logging.Logger: logger instance
    """
    # Return Cached logger
    try:
        logger = _CACHE['logger']

    # Initialize logger on first call
    except KeyError:
        import logging
        logger = logging.getLogger("acceleratorAPI")
        logger.setLevel(logging.INFO)
        logger.addHandler(logging.NullHandler())

    if stdout:
        import logging
        logger.addHandler(logging.StreamHandler())

    return logger
