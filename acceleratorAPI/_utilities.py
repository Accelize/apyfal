# coding=utf-8
"""Generic utilities used in acceleratorAPI code"""

import abc
import ast
import json
import os
import re
import sys
import time

import requests


_CACHE = dict()  # Store some cached values


# Python 2 compatibility
if sys.version_info[0] >= 3:
    # Python 3: redirect name to existing objects
    makedirs = os.makedirs
    ABC = abc.ABC

else:
    # Python 2: defines back ports

    # Back port of "os.makedirs" with exists_ok
    def makedirs(name, mode=0o777, exist_ok=False):
        """
        Super-mkdir; create a leaf directory and all intermediate ones. Works like
        mkdir, except that any intermediate path segment (not just the rightmost)
        will be created if it does not exist. If the target directory already
        exists,

        Args:
            name (str): Path
            mode (int): The mode parameter is passed to os.mkdir();
                see the os.mkdir() description for how it is interpreted.
            exist_ok (bool): Don't raises error if target directory already exists.

        Raises:
            OSError: if exist_ok is False and if the target directory already exists.
        """
        try:
            os.makedirs(name, mode)
        except OSError:
            if not exist_ok or not os.path.isdir(name):
                raise

    # Back port of "abc.ABC" base abstract class
    ABC = abc.ABCMeta('ABC', (object,), {})


class Timeout:
    """Context manager to handle timeout in loop.

    Use "reached" method to check if timeout is reached.

    Args:
        timeout (float): Timeout value in seconds.
        sleep (float): Wait duration in seconds when check
            for reached method if timeout not reached.
    """

    def __init__(self, timeout, sleep=1.0):
        self._timeout = timeout
        self._start_time = time.time()
        self._sleep = sleep

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        pass

    def reached(self):
        """
        Check if timeout reached.

        Returns:
            bool: True if timeout reached.
        """
        if time.time() - self._start_time > self._timeout:
            return True
        time.sleep(self._sleep)
        return False


def http_session(max_retries=2, https=True):
    """
    Instantiate HTTP session

    Args:
        max_retries (int): The maximum number of retries each connection should attempt
        https (bool): If True, enables HTTPS and HTTP support. Else only HTTP support.

    Returns:
        requests.Session: Http session
    """
    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(max_retries=max_retries)
    session.mount('http://', adapter)
    if https:
        session.mount('https://', adapter)
    return session


def check_url(url, timeout=0.0, max_retries=0, sleep=0.5):
    """
    Checking if an HTTP is up and running.

    Will attempt to connect during "timeout", every "sleep" time
    with "max_retries" retries per attempt.

    Args:
        url (str): URL
        timeout (float): Timeout value in seconds.
        max_retries (int): Number of tries per connexion attempt.
        sleep (float): Period between connexion attempt in seconds.

    Returns:
        bool: True if success, False elsewhere
    """
    session = http_session(max_retries=max_retries, https=False)
    with Timeout(timeout, sleep=sleep) as timeout:
        while True:
            try:
                if session.get(url).status_code == 200:
                    return True
            except requests.RequestException:
                pass
            if timeout.reached():
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


def get_host_public_ip():
    """
    Find current host IP address.

    Returns:
        str: IP address in "XXX.XXX.XXX.XXX/32" format.
    """
    # Lazy import since not always used
    import ipgetter
    return "%s/32" % ipgetter.myip()


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

    # Create if not exists
    makedirs(ssh_dir, 0o700, exist_ok=True)

    # Find SSH key file path
    ssh_files = os.listdir(ssh_dir)

    # Check if SSH file already exists
    # and increment name if another file
    # with different content exists
    index = 1
    while True:
        # File name
        ssh_key_file = "%s%s.pem" % (
            ssh_key, ('_%d' % index) if index > 1 else '')
        key_filename = os.path.join(ssh_dir, ssh_key_file)

        # File with same name exists
        if ssh_key_file in ssh_files:
            # File already exist, returns
            with open(key_filename, 'rt') as key_file:
                if key_file.read() == key_content:
                    return
            # Else increment name
            index += 1

        # File don't exists
        else:
            break

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
        logger.addHandler(logging.NullHandler())

    if stdout:
        import logging
        logger.addHandler(logging.StreamHandler())
        logger.setLevel(logging.INFO)

    return logger
