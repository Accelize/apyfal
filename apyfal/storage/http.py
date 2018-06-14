# coding=utf-8
"""Access files over HTTP"""

from shutil import copyfileobj as _copyfileobj

# TODO: Raise Apyfal exception
import apyfal.exceptions as _exc
from apyfal.storage import Storage as _Storage
from apyfal._utilities import http_session as _http_session


class HTTPStorage(_Storage):
    """Files access over HTTP

    apyfal.storage.copy URL: "http://path"

    Args:
        storage_type (str): Type of storage. Default to "HTTP".
    """
    #: Storage type
    NAME = 'HTTP'

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

    def copy_to_stream(self, source, stream):
        """
        Copy a file from storage to binary stream.

        Args:
            source (str): Source URL.
            stream (file-like object): Destination binary stream.
        """
        response = _http_session().get(source, stream=True)
        response.raise_for_status()
        _copyfileobj(response.raw, stream)

    def copy_from_stream(self, stream, destination):
        """
        Copy a file to storage from binary stream.

        Args:
            stream (file-like object): Source binary stream.
            destination (str): Destination URL.
        """
        response = _http_session().post(destination, data=stream)
        response.raise_for_status()
