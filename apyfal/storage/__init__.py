# coding=utf-8
"""Data storage management"""

from abc import abstractmethod as _abstractmethod
from shutil import copy as _copy
import tempfile as _tempfile

import apyfal.configuration as _cfg
import apyfal.exceptions as _exc
import apyfal._utilities as _utl

# Storage name aliases
_ALIASES = {
    # "host" only available on call from REST client
    'host': 'file',

    # Schemes variants
    'https': 'http',
}


# Registered storage
class _StorageHook(dict):
    """Hook of available storage

    Storage are by default lazy instantiated on needs"""

    def __missing__(self, storage_type):
        # Try to register if not already exists
        return self.register(storage_type)

    def register(self, storage_type, **parameters):
        """Register a new storage.

        Args:
            storage_type (str): storage type
            parameters: storage parameters
        """
        storage = Storage(storage_type=storage_type, **parameters)
        self[storage.storage_id] = storage
        return storage


_STORAGE = _StorageHook()


def register(storage_type, **parameters):
    """Register a new storage to be used with "copy".

    Args:
        storage_type (str): storage type
        parameters: storage parameters
            (see targeted storage class for more information)
    """
    _STORAGE.register(storage_type, **parameters)


def _parse_host_url(url):
    """Return scheme and path from URL:

    URL = scheme://path

    If URL has no scheme, "file" scheme is inferred.

    Scheme is returned from host point of view:
    "host" scheme is converted to "file" scheme.

    Args:
        url (str): URL to parse

    Returns:
        tuple of str: (scheme, path)
    """
    split_url = url.split('://', 1)
    try:
        # Path with scheme
        scheme = split_url[0].lower()
        path = split_url[1]
    except IndexError:
        # Path without scheme are "file://"
        return 'file', url

    # Get scheme from alias
    scheme = _ALIASES.get(scheme, scheme)

    # Returns result
    # Some storage needs full URL as path
    return scheme, url if scheme in ('http', ) else path


def copy(source, destination):
    """
    Copy a file from source to destination. Support copy
    over different kind of storage that must be first
    registered with "register_storage" function.

    Work with URL with format "scheme://path"

    Common schemes are (Registered by default):

    - "file://" or no scheme: Client local file.
    - "host://": Host local file (Available only on client
        if client is not host).
    - "http://" or "https://": File access over HTTP.
    - "ftp://" or "ftps://": File access over FTP.

    Some storage use advanced same, basic form is
    "StorageType://path" with StorageType the storage type
    defining this storage.

    Some storage use sub levels, this is separated from
    storage type with dot ".":
    "StorageType.SubLevel://path"

    See target storage class documentation for more information.

    Args:
        source (str): Source URL.
        destination (str): Destination URL.
    """
    # Analyses URLs
    src_scheme, src_path = _parse_host_url(source)
    dst_scheme, dst_path = _parse_host_url(destination)

    # Performs operation
    if src_scheme == 'file' and dst_scheme == 'file':
        # Local to local
        _copy(src_path, dst_path)

    elif src_scheme == 'file' and dst_scheme != 'file':
        # Local to storage
        _STORAGE[dst_scheme].copy_from_local(src_path, dst_path)

    elif src_scheme != 'file' and dst_scheme == 'file':
        # Storage to local
        _STORAGE[src_scheme].copy_to_local(src_path, dst_path)

    else:
        # Storage to storage
        _STORAGE[dst_scheme].copy_from_storage(
            _STORAGE[src_scheme], src_path, dst_path)


class Storage(_utl.ABC):
    """Base storage class

    This is also a factory which instantiate host subclass related to
    specified cases.

    Args:
        storage_type (str): Type of storage.
    """
    #: Storage type name (str), must be the same as expected "storage_type" argument value
    NAME = None

    #: Link to Storage documentation or website
    DOC_URL = ''

    def __new__(cls, *args, **kwargs):
        # If call from a subclass, instantiate this subclass directly
        if cls is not Storage:
            return object.__new__(cls)

        storage_type = (_utl.get_first_arg(
            args, kwargs, 'storage_type') or '').split('.', 1)[0].lower()

        # Get Storage subclass
        return _utl.factory(
            cls, storage_type, 'storage_type', _exc.StorageConfigurationException)

    def __init__(self, storage_type=None, config=None, **_):
        self._storage_type = storage_type or self.NAME
        self._config = _cfg.create_configuration(config)

    @property
    def storage_id(self):
        """Storage ID representing this storage.

        Returns:
            str: Storage ID."""
        return self.NAME.lower()

    def copy_to_local(self, source, local_path):
        """
        Copy a file from storage to local.

        Args:
            source (str): Source URL.
            local_path (str): Local destination path.
        """
        with open(local_path, 'wb') as file:
            self.copy_to_stream(source, file)

    def copy_from_local(self, local_path, destination):
        """
        Copy a file to storage from local.

        Args:
            local_path (str): Local source path.
            destination (str): Destination URL
        """
        with open(local_path, 'rb') as file:
            self.copy_from_stream(file, destination)

    @_abstractmethod
    def copy_to_stream(self, source, stream):
        """
        Copy a file from storage to binary stream.

        Args:
            source (str): Source URL.
            stream (file-like object): Destination binary stream.
        """

    @_abstractmethod
    def copy_from_stream(self, stream, destination):
        """
        Copy a file to storage from binary stream.

        Args:
            stream (file-like object): Source binary stream.
            destination (str): Destination URL.
        """

    def copy_from_storage(self, storage, source, destination):
        """
        Copy from another storage to this one.

        Args:
            storage (Storage): Storage from where copy.
            source (str): Source path on other storage.
            destination (str): Destination path on this storage.
        """
        # Tries to use a storage specific method
        try:
            copy_from_storage = getattr(
                self, '_copy_from_%s' % storage.NAME.lower())

        # Uses spooled temporary file copy
        except AttributeError:
            copy_from_storage = self._copy_from_temporary

        # Performs copy
        return copy_from_storage(storage, source, destination)

    def _copy_from_temporary(self, storage, source, destination):
        """
        Copy from another storage to this one using spooled temporary file on
        this machine.

        Args:
            storage (Storage): Storage from where copy.
            source (str): Source path
            destination (str): Destination path
        """
        # TODO: Compute max_size to use instead to use fixed 1GB value (psutil)
        with _tempfile.SpooledTemporaryFile(max_size=1e9) as stream:
            storage.copy_to_stream(source, stream)
            stream.seek(0)
            self.copy_from_stream(stream, destination)
