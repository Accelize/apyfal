# coding=utf-8
"""Data storage I/O

Support I/O over different kind of storage that must
be first mounted.

Theses features are provided by the "pycosio". Path are automatically handled
with pycosio in Apyfal to provides automatic support of cloud storage.

Mount storage:
    Storage defined in configuration are automatically mounted
    on first call. It is possible to manually mount new storage
    with "mount" function.

The Apyfal configuration file is used to automatically mount all known
storage on start up.

Storage URL format:
    All operations works with URL with format "scheme://path"

    Common schemes are (mounted by default):

    - "file://" or no scheme: Client local file.
    - "host://": Host local file (Available only on REST client).
    - "http://" or "https://": File access over HTTP.

    Some storage use advanced same, basic form is
    "StorageType://path" with StorageType the storage type
    defining this storage.

See target storage class documentation for more information.
"""
from concurrent.futures import (
    ThreadPoolExecutor as _ThreadPoolExecutor, wait as _wait)
from contextlib import contextmanager as _contextmanager
from copy import deepcopy as _deepcopy
from sys import version_info as _py

import pycosio as _pycosio

import apyfal.configuration as _cfg
import apyfal._utilities as _utl
import apyfal.exceptions as _exc


@_contextmanager
def open(url, mode="rb", encoding=None, errors=None, newline=None):
    """
    Open file and return a corresponding file object.

    Args:
        url (path-like object or file-like object): URL or file object to open.
        mode (str): Mode in which the file is opened
            (Works like standard library open mode).
            Support at least 'r' (read), 'w' (write), 'b' (binary),
            't' (text) modes, eventually more depending on source file.
        encoding (str): with text  mode,
            encoding used to decode or encode the file.
        errors (str): with text mode, specifies how encoding and
            decoding errors are to be handled
        newline (str): Controls how universal newlines mode works.

    Returns:
        file-like object: Opened object handle
    """
    with _pycosio.open(url, mode=mode, encoding=encoding, errors=errors,
                       newline=newline) as stream:
        yield stream


def copy(source, destination):
    """
    Copy a file from source to destination.

    Args:
        source (path-like object or file-like object): Source URL.
            Can be apyfal.storage URL, paths, file-like object.
        destination (path-like object or file-like object): Destination URL.
            Can be apyfal.storage URL, paths, file-like object.
    """
    _pycosio.copy(source, destination)


def mount(storage_type, **kwargs):
    """Mount a new storage.

    Args:
        storage_type (str): storage type
        kwargs: Storage keywords argument
            (see targeted storage class for more information)
    """
    _Storage(storage_type=storage_type, **kwargs).mount()


def parse_url(url, host=True):
    """Return storage_type and path from URL.

    If URL has no scheme, "file" scheme is inferred.

    If URL is a file-like object, returns "stream" as storage_type.

    Args:
        url (path-like object or file-like object): URL to parse
        host (bool): If True, Scheme is returned from
            host point of view: "host" scheme is converted
            to "file" scheme.

    Returns:
        tuple of str: (storage_type, path)
    """
    if hasattr(url, 'read'):
        return 'stream', url

    url = _utl.fsdecode(url)
    split_url = url.split('://', 1)
    try:
        # Path with scheme
        scheme = split_url[0].lower()
        path = split_url[1]
    except IndexError:
        # Path without scheme are "file://"
        return 'file', url

    # Host storage_type special case
    if scheme == 'host':
        return 'file' if host else scheme, path

    # Returns result
    return scheme, path


class _Storage(object):
    # Python 2: requires new style class (inherit fro object) to use __new__
    """Base storage class
    This is also a factory which instantiate host subclass related to
    specified cases.

    Args:
        storage_type (str): Type of storage.
        config (apyfal.configuration.Configuration, path-like object or file-like object):
            If not set, will search it in current working directory, in current
            user "home" folder. If none found, will use default configuration
            values.
            Path-like object can be path, URL or cloud object URL.
        unsecure (bool): if True (default) disables TLS/SSL/HTTPS for transfer.
            This can improve performance, but makes connection insecure.
        client_id (str): Storage access key ID.
        secret_id (str): Storage secret access Key.
        storage_parameters (dict): Extra "storage_parameters".
            See "pycosio.mount".
    """
    #: Name (str), Linked to apyfal.host NAME
    NAME = None

    #: Storage name (str). Name in "pycosio"
    STORAGE_NAME = None

    #: Link to Storage documentation or website (str)
    DOC_URL = ''

    #: Extra URL prefix (str), For shorter URL
    EXTRA_URL_PREFIX = None

    #: Storage parameters template (dict)
    STORAGE_PARAMETERS = {}

    def __new__(cls, *args, **kwargs):
        # If call from a subclass, instantiate this subclass directly
        if cls is not _Storage:
            return object.__new__(cls)

        # Get storage_type from configuration or argument
        storage_type = (_utl.get_first_arg(
            args, kwargs, 'storage_type') or '').split('.', 1)[0].lower()

        # Get _Storage subclass
        return _utl.factory(
            cls, storage_type, 'storage_type',
            _exc.StorageConfigurationException)

    def __init__(self, storage_type=None, config=None,
                 client_id=None, secret_id=None, unsecure=None,
                 storage_parameters=None, **_):
        self._storage_type = storage_type or self.STORAGE_NAME
        self._storage_parameters = storage_parameters or dict()
        self._config = _cfg.create_configuration(config)

        self._client_id = self._from_config('client_id', client_id)
        self._secret_id = self._from_config('secret_id', secret_id)
        self._unsecure = True if ((self._from_config(
            'unsecure', unsecure)) in ('True', True)) else False

    def _from_config(self, key, value=None):
        """Get value from configuration file.
        Look in following section in this order:
        storage.provider, host.provider

        Args:
            key (str): Key to find
            value: If specified and not None, return this value.

        Returns:
            str: value
        """
        for candidat in (
                value, self._config['storage.%s' % self._storage_type][key],
                self._config['storage.%s' % self.STORAGE_NAME][key],
                self._config['host.%s' % self.NAME or self.STORAGE_NAME][key]):
            if candidat is not None:
                return candidat

    def _update_parameter(self, parameters):
        """Update parameter template with attributes values.

        Args:
            parameters (dict): parameters to update"""

        for key, value in parameters.items():
            # Update sub parameters
            if isinstance(value, dict):
                self._update_parameter(value)

            # Update value
            elif isinstance(value, str) and value.startswith('self.'):
                parameters[key] = getattr(self, value.split('.', 1)[1])

    def mount(self):
        """Mount storage."""
        storage_parameters = _deepcopy(self.STORAGE_PARAMETERS)
        self._update_parameter(storage_parameters)
        _utl.recursive_update(storage_parameters, self._storage_parameters)
        return _pycosio.mount(
            storage=self.STORAGE_NAME, extra_url_prefix=self.EXTRA_URL_PREFIX,
            storage_parameters=storage_parameters, unsecure=self._unsecure)


# Automatically mounts known storage from configuration
def _auto_mount():
    """mounts from configuration"""
    # Get configuration
    config = _cfg.Configuration()

    # Finds possibles storage
    to_mount = set()
    name = config['host']['host_type']
    if name:
        to_mount.add(name)
    for section in config:
        if section.startswith('host.') or section.startswith('storage.'):
            name = section.split('.', 1)[1]
            if name:
                to_mount.add(name)

    if to_mount:
        # Tries to mount storage
        if _py[0] == 2:
            # On Python 2: Seem to have a deadlock on import if use of
            # ThreadPoolExecutor
            for storage_type in to_mount:
                try:
                    mount(storage_type=storage_type, config=config)
                except (ImportError, _exc.AcceleratorException):
                    continue
            return

        futures = []
        with _ThreadPoolExecutor(max_workers=len(to_mount)) as executor:
            for storage_type in to_mount:
                try:
                    storage = _Storage(storage_type=storage_type, config=config)
                except (ImportError, _exc.AcceleratorException):
                    continue
                futures.append(executor.submit(storage.mount))

            # Waits completion and hide exceptions silently
            _wait(futures)


_auto_mount()
del _auto_mount
