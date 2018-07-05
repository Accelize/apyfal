# coding=utf-8
"""Data storage I/O

Support I/O over different kind of storage that must
be first registered.

Register storage:
    Storage defined in configuration are automatically registered
    on first call. It is possible to manually register new storage
    with "register" function.

Storage URL format:
    All operations works with URL with format "scheme://path"

    Common schemes are (Registered by default):

    - "file://" or no scheme: Client local file.
    - "host://": Host local file (Available only on REST client).
    - "http://" or "https://": File access over HTTP.

    Some storage use advanced same, basic form is
    "StorageType://path" with StorageType the storage type
    defining this storage.

    Some storage use sub levels, this is separated from
    storage type with dot ".":
    "StorageType.SubLevel://path"

See target storage class documentation for more information.
"""

from abc import abstractmethod as _abstractmethod
from contextlib import contextmanager as _contextmanager
from io import TextIOWrapper as _TextIOWrapper, open as _io_open
from shutil import copy as _copy, copyfileobj as _copyfileobj
import tempfile as _tempfile

from psutil import virtual_memory as _virtual_memory

import apyfal.configuration as _cfg
import apyfal.exceptions as _exc
import apyfal._utilities as _utl

__all__ = ['open', 'copy', 'parse_url', 'Storage']

# Storage name aliases
_ALIASES = {
    # Storage type/schemes variants
    'https': 'http',
}

# Needs full URL as path
_NEED_FULL_URL = ['http']


# Registered storage
class _StorageHook(dict):
    """Hook of available storage

    Storage are by default lazy instantiated on needs"""

    def __missing__(self, storage_type):
        # Try to register if not already exists
        if storage_type in ('file', 'host', 'stream'):
            raise ValueError('Invalid storage_type "%s"' % storage_type)
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
    """Register a new storage.

    Args:
        storage_type (str): storage type
        parameters: storage parameters
            (see targeted storage class for more information)
    """
    return _STORAGE.register(storage_type, **parameters)


def parse_url(url, host=True):
    """Return storage_type and path from URL.

    If URL has no scheme, "file" scheme is inferred.

    If URL is a file-like object, returns "stream" as storage_type.

    Args:
        url (str or file-like object): URL to parse
        host (bool): If True, Scheme is returned from
            host point of view: "host" scheme is converted
            to "file" scheme.

    Returns:
        tuple of str: (storage_type, path)
    """
    if not isinstance(url, str):
        return 'stream', url

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

    # Get storage_type from scheme
    storage_type = _ALIASES.get(scheme, scheme)

    # Some storage needs full URL as path
    if storage_type in _NEED_FULL_URL:
        path = url

    # Returns result
    return storage_type, path


@_contextmanager
def _io_wrapper(stream, mode, encoding=None, errors=None, newline=None):
    """Yield text or binary stream wrapper depending mode.

    Args:
        stream (file-like object): Stream to wrap.
        mode (str): Mode in which the file is opened
            (Works like standard library open mode).
            Support at least 'r' (read), 'w' (write), 'b' (binary),
            't' (text) modes, eventually more depending on source file.
        encoding (str): with text  mode,
            encoding used to decode or encode the file.
        errors (str): with text mode, specifies how encoding and
            decoding errors are to be handled
        newline (str): Controls how universal newlines mode works.

    Yields:
        file-like object: Wrapped stream.
    """
    if "t" in mode:
        text_stream = _TextIOWrapper(
            stream, encoding=encoding, errors=errors, newline=newline)
        yield text_stream
        text_stream.flush()
    else:
        yield stream


class _SpooledTemporaryFile(_tempfile.SpooledTemporaryFile):
    """Temporary file wrapper, specialized to switch from BytesIO
    or StringIO to a real file when it exceeds a certain size or
    when a fileno is needed.
    """

    def __init__(self, *args, **kwargs):
        # Set max_size to 90% of available memory by default
        kwargs.setdefault(
            'max_size', int(_virtual_memory().available * 0.90))
        _tempfile.SpooledTemporaryFile.__init__(self, *args, **kwargs)

    # Python 3.8 back port:
    # Add all io.IOBase abstract methods support

    def readable(self):
        """
        Returns True if the stream can be read from.
        If False, read() will raise OSError.

        Returns:
            bool: readable.
        """
        try:
            return self._file.readable()
        except AttributeError:
            # Python 2 Compatibility:
            # Assume its True as this is OK in our use case.
            return True

    def seekable(self):
        """
        Return True if the stream supports random access.
        If False, seek(), tell() and truncate() will raise OSError.

        Returns:
            bool: Seekable
        """
        try:
            return self._file.seekable()
        except AttributeError:
            # Python 2 Compatibility:
            # Assume its True as this is OK in our use case.
            return True

    def writable(self):
        """
        Return True if the stream supports writing.
        If False, write() and truncate() will raise OSError.

        Returns:
            bool: Writable
        """
        try:
            return self._file.writable()
        except AttributeError:
            # Python 2 Compatibility:
            # Assume its True as this is OK in our use case.
            return True


# Create apyfal.storage.open function, but keep reference to builtin open
_stdlib_open = open


@_contextmanager
def open(url, mode="rb", encoding=None, errors=None, newline=None):
    """
    Open file and return a corresponding file object.

    Args:
        url (str or file-like object): URL or file object to open.
            Can be apyfal.storage URL, paths, file-like object.
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
    # Parses URL
    scheme, path = parse_url(url)
    try:
        storage = _STORAGE[scheme]

    except ValueError:
        # Open file as stream
        if scheme == 'file':
            with _io_open(path, mode=mode, encoding=encoding,
                          errors=errors, newline=newline) as stream:
                yield stream

        # Open Stream
        elif scheme == 'stream':
            with _io_wrapper(path, mode, encoding,
                             errors, newline) as wrapped:
                yield wrapped

    # Open storage as stream
    else:
        with _SpooledTemporaryFile() as stream:
            if 'r' in mode:
                storage.copy_to_stream(path, stream)
                stream.seek(0)

            with _io_wrapper(stream, mode, encoding,
                             errors, newline) as wrapped:
                yield wrapped

            if 'w' in mode:
                stream.seek(0)
                storage.copy_from_stream(stream, path)


def copy(source, destination):
    """
    Copy a file from source to destination.

    Args:
        source (str or file-like object): Source URL.
            Can be apyfal.storage URL, paths, file-like object.
        destination (str or file-like object): Destination URL.
            Can be apyfal.storage URL, paths, file-like object.
    """

    # Parses URLs
    src_scheme, src_path = parse_url(source)
    dst_scheme, dst_path = parse_url(destination)

    # Performs operation
    if src_scheme == 'file' and dst_scheme == 'file':
        # Local to local
        _copy(src_path, dst_path)

    elif src_scheme == 'stream' and dst_scheme == 'stream':
        # Stream to stream
        _copyfileobj(src_path, dst_path)

    elif src_scheme == 'stream' and dst_scheme == 'file':
        # Stream to local
        with _stdlib_open(dst_path, 'wb') as dst_file:
            _copyfileobj(src_path, dst_file)

    elif src_scheme == 'file' and dst_scheme == 'stream':
        # Local to stream
        with _stdlib_open(src_path, 'rb') as src_file:
            _copyfileobj(src_file, dst_path)

    elif src_scheme == 'stream':
        # Stream to storage
        _STORAGE[dst_scheme].copy_from_stream(src_path, dst_path)

    elif dst_scheme == 'stream':
        # Storage to stream
        _STORAGE[src_scheme].copy_to_stream(src_path, dst_path)

    elif src_scheme == 'file':
        # Local to storage
        _STORAGE[dst_scheme].copy_from_local(src_path, dst_path)

    elif dst_scheme == 'file':
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
        config (str or apyfal.configuration.Configuration or file-like object):
            Can be Configuration instance, apyfal.storage URL, paths, file-like object.
            If not set, will search it in current working directory, in current
            user "home" folder. If none found, will use default configuration values.
    """
    #: Storage type name (str), must be the same as expected "storage_type" argument value
    NAME = None

    #: Link to Storage documentation or website
    DOC_URL = ''

    def __new__(cls, *args, **kwargs):
        # If call from a subclass, instantiate this subclass directly
        if cls is not Storage:
            return object.__new__(cls)

        # Get storage_type from configuration or argument
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
        with _stdlib_open(local_path, 'wb') as file:
            self.copy_to_stream(source, file)

    def copy_from_local(self, local_path, destination):
        """
        Copy a file to storage from local.

        Args:
            local_path (str): Local source path.
            destination (str): Destination URL
        """
        with _stdlib_open(local_path, 'rb') as file:
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
        with _SpooledTemporaryFile() as stream:
            storage.copy_to_stream(source, stream)
            stream.seek(0)
            self.copy_from_stream(stream, destination)
