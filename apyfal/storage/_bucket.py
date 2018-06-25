# coding=utf-8
"""Cloud Storage Bucket"""

from abc import abstractmethod as _abstractmethod

from apyfal.storage import Storage as _Storage
import apyfal.configuration as _cfg


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

    def __init__(self, config=None,
                 client_id=None, secret_id=None,
                 region=None, bucket_name=None, **kwargs):
        config = _cfg.create_configuration(config)
        _Storage.__init__(self, config=config, **kwargs)

        # Default some attributes
        self._bucket_name = bucket_name
        self._session = None

        # Read configuration from file
        section = self.storage_id
        self._client_id = config.get_default(
            section, 'client_id', overwrite=client_id)
        self._secret_id = config.get_default(
            section, 'secret_id', overwrite=secret_id)
        self._region = config.get_default(
            section, 'region', overwrite=region)

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
    def copy_to_local(self, source, local_path):
        """
        Copy a file from storage to local.

        Args:
            source (str): Source URL.
            local_path (str): Local destination path.
        """

    @_abstractmethod
    def copy_from_local(self, local_path, destination):
        """
        Copy a file to storage from local.

        Args:
            local_path (str): Local source path.
            destination (str): Destination URL
        """

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
