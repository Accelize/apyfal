# coding=utf-8
"""Generic utilities used in apyfal code"""

import abc
import collections
from contextlib import contextmanager
from importlib import import_module
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


def factory(cls, cls_type, parameter_name, exc_type):
    """Find and instantiate target subclass by its name.

    Target subclass must follow rules:
    - module containing subclass must be in a submodule of the
      one containing the parent class.
    - module containing subclass name must be cls_type.lower()
    - Class must have a class attribute NAME matching cls_type.

    Args:
        cls (class): Parent class.
        cls_type (str): Target subclass.
        parameter_name (str): cls_type parameter name.
        exc_type (apyfal.exceptions.AcceleratorException subclass):
            Exception to raise if not found.

    Returns:
        cls subclass: Subclass of cls
    """
    # Not target subclass, instantiate parent class
    if cls_type is None:
        return object.__new__(cls)

    cls_type_low = cls_type.lower()

    # Finds module containing target subclass
    module_name = '%s.%s' % (cls.__module__, cls_type_low)
    try:
        module = import_module(module_name)
    except ImportError as exception:
        if cls_type_low in str(exception):
            # If ImportError for current module name, may be
            # a configuration error.
            raise exc_type(
                "No module '%s' for '%s' %s" % (
                    module_name, cls_type, parameter_name))
        # ImportError of another module, raised as it
        raise

    # Finds target subclass
    for name in dir(module):
        member = getattr(module, name)
        try:
            if getattr(member, 'NAME').lower() == cls_type_low:
                break
        except AttributeError:
            continue
    else:
        raise exc_type(
            "No class found in '%s' for '%s' %s" % (
                module_name, cls_type, parameter_name))

    # Instantiates target subclass
    return object.__new__(member)


def get_first_arg(args, kwargs, name):
    """Returns named argument assuming it is in first position.
    Returns None if not found.

    Args:
        args (tuple or list): args from function.
        kwargs (dict): kwargs from function.
        name (str): argument name
    """
    try:
        return kwargs[name]
    except KeyError:
        try:
            return args[0]
        except IndexError:
            return None


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


@contextmanager
def handle_request_exceptions(exc_type):
    """Handle Request exceptions and raise specific exception.

    Args:
        exc_type (apyfal.exceptions.AcceleratorException subclass):
            Exception type to raise.
    """
    try:
        yield
    except requests.RequestException as exception:
        raise exc_type(exc=exception)


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


def get_host_public_ip(max_tries=10, validation_sample=3):
    """
    Find current host IP address.

    Args:
        max_tries (int): Number of tries.
        validation_sample (int): Number of service to
            request that must return same result to
            validate IP address.

    Returns:
        str: IP address in "XXX.XXX.XXX.XXX/32" format.
    """
    # Lazy import since not always used
    from ipgetter import myip

    # Gets IP address from multiple sources and
    # checks result consistency before returning one
    for _ in range(max_tries):
        ip_addresses = set(
            myip() for _ in range(validation_sample))
        if len(ip_addresses) == 1:
            ip_address = ip_addresses.pop()
            if ip_address:
                return "%s/32" % ip_address
    raise OSError('Unable to get public IP address')


def recursive_update(to_update, update):
    """
    Recursively updates nested directories.

    Args:
        to_update (dict or collections.Mapping):
            dict to update.
        update (dict or collections.Mapping):
            dict containing new values.

    Returns:
        dict: to_update
        """
    for key, value in update.items():
        if isinstance(value, collections.Mapping):
            value = recursive_update(
                to_update.get(key, {}), value)
        to_update[key] = value
    return to_update


def create_key_pair_file(key_pair, key_content):
    """
    Create SSH key file.

    Args:
        key_pair (str): key name
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
        key_pair_file = "%s%s.pem" % (
            key_pair, ('_%d' % index) if index > 1 else '')
        key_filename = os.path.join(ssh_dir, key_pair_file)

        # File with same name exists
        if key_pair_file in ssh_files:
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


def gen_msg(message_id, *args):
    """
    Provides pre-generated text messages.

    Args:
        message_id (str):
        args (str): Arguments which are merged into message using
            the string formatting operator.

    Returns:
        str: message
    """
    # Get message
    message = dict(
        not_found_named="'%s' not found: %s",
        no_find="Unable to find %s",
        no_find_named="Unable to find %s '%s'",
        no_host_found='No host found. Please check your configuration.',
        no_instance_ip="Unable to find instance IP",
        no_instance_id="Unable to find instance '%s'",
        no_instance="Unable to find instance",
        no_credentials="Accelize client ID and secret ID are mandatory.",
        created_named="Created %s '%s'",
        created_failed="Unable to create %s",
        created_failed_named="Unable to create %s '%s'",
        accelize_generated="Generated by Apyfal",
        attached_to="Attached %s '%s' to %s '%s'",
        authorized_ip="Authorized '%s' in security group '%s'",
        timeout="Timed out while waiting instance %s",
        timeout_status="Timed out while waiting instance %s, last status: %s",
        unable_to="Unable to %s instance",
        unable_to_named="Unable to %s %s",
        unable_to_status="Unable to %s instance, last status: %s",
        unable_find_from="Unable to find %s '%s', please contact %s.",
        unable_reach_url="Unable to reach URL '%s'"
    )[message_id]

    # Merge arguments
    if args:
        message %= args

    return message


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
        logger = logging.getLogger("apyfal")
        logger.addHandler(logging.NullHandler())

    if stdout:
        import logging
        logger.addHandler(logging.StreamHandler())
        logger.setLevel(logging.INFO)

    return logger
