# coding=utf-8
"""Cloud Storage Bucket"""

from abc import abstractmethod as _abstractmethod

from apyfal.storage import Storage as _Storage


class BucketStorage(_Storage):
    """Cloud storage Bucket

    apyfal.storage.copy URL: "CSPName.BucketName://KeyToObject"

    Args:
        storage_type (str): Cloud service provider name.
        config (str or apyfal.configuration.Configuration): Configuration file path or instance.
            If not set, will search it in current working directory, in current
            user "home" folder. If none found, will use default configuration values.
        client_id (str): CSP Access Key ID.
        secret_id (str): CSP Secret Access Key.
        region (str): CSP region.
        bucket_name (str): Name on the bucket on CSP.
    """

    def __init__(self,
                 client_id=None, secret_id=None,
                 region=None, bucket_name=None, **kwargs):
        _Storage.__init__(self, **kwargs)

        # Get bucket name from storage_type
        try:
            self._storage_type, self._bucket_name = self._storage_type.split('.', 1)
        except ValueError:
            self._bucket_name = None
        self._bucket_name = bucket_name or self._bucket_name

        # Default some attributes
        self._session = None

        # Read configuration from file
        section = 'storage.%s' % self.storage_id
        self._client_id = client_id or self._config[section]['client_id']
        self._secret_id = secret_id or self._config[section]['secret_id']
        self._region = region or self._config[section]['region']

    @property
    def bucket(self):
        """Bucket name

        Returns:
            str: bucket name."""
        return self._bucket_name

    @property
    def storage_id(self):
        """_Storage ID representing this storage.

        Returns:
            str: _Storage ID."""
        return ('%s.%s' % (
            self.NAME, self._bucket_name)).lower()

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
