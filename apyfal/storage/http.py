# coding=utf-8
"""Access files over HTTP"""

from shutil import copyfileobj as _copyfileobj

import apyfal.exceptions as _exc
from apyfal.storage import Storage as _Storage
import apyfal._utilities as _utl


class HTTPStorage(_Storage):
    """Files access over HTTP

    apyfal.storage.copy URL: "http://path"

    Args:
        storage_type (str): Type of storage. Default to "HTTP".
        config (str or apyfal.configuration.Configuration): Configuration file path or instance.
            If not set, will search it in current working directory, in current
            user "home" folder. If none found, will use default configuration values.
    """
    #: Storage type
    NAME = 'HTTP'

    def copy_to_stream(self, source, stream):
        """
        Copy a file from storage to binary stream.

        Args:
            source (str): Source URL.
            stream (file-like object): Destination binary stream.
        """
        with _utl.handle_request_exceptions(_exc.StorageRuntimeException):
            response = _utl.http_session().get(source, stream=True)
            response.raise_for_status()
        _copyfileobj(response.raw, stream)

    def copy_from_stream(self, stream, destination):
        """
        Copy a file to storage from binary stream.

        Args:
            stream (file-like object): Source binary stream.
            destination (str): Destination URL.
        """
        with _utl.handle_request_exceptions(_exc.StorageRuntimeException):
            response = _utl.http_session().post(destination, data=stream)
            response.raise_for_status()
