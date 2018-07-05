# coding=utf-8
"""Cloud Storage Bucket"""

from abc import abstractmethod as _abstractmethod

from apyfal.storage import Storage as _Storage


class BucketStorage(_Storage):
    """Cloud storage Bucket

    apyfal.storage URL: "CSPName://BucketName/KeyToObject"

    Args:
        storage_type (str): Cloud service provider name.
        config (str or apyfal.configuration.Configuration or file-like object):
            Can be Configuration instance, apyfal.storage URL, paths, file-like object.
            If not set, will search it in current working directory, in current
            user "home" folder. If none found, will use default configuration values.
        client_id (str): CSP Access Key ID.
        secret_id (str): CSP Secret Access Key.
    """

    #: Linked apyfal.host NAME, if not different from NAME
    HOST_NAME = None

    def __init__(self, client_id=None, secret_id=None, **kwargs):
        _Storage.__init__(self, **kwargs)

        # Default some attributes
        self._session = None

        # Read configuration from file, start to search
        self._client_id = self._from_config('client_id', client_id)
        self._secret_id = self._from_config('secret_id', secret_id)

    def _from_config(self, key, value=None):
        """Get value from configuration file.
        Look in following section in this order:
        storage.provider.bucket, storage.provider, host.provider

        Args:
            key (str): Key to find
            value (str): If specified and not None, return this value.

        Returns:
            str: value
        """
        return (value or
                self._config['storage.%s' % self.NAME][key] or
                self._config['host.%s' % self.HOST_NAME or self.NAME][key])

    @staticmethod
    def _get_bucket(path):
        """
        Get bucket and file path from global path.

        Args:
            path (str): path

        Returns:
            tuple of str: bucket, file path
        """
        return path.split('/', 1)

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
