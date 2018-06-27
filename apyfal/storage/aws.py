# coding=utf-8
"""Amazon Web Services S3"""

import boto3 as _boto3

from apyfal.storage._bucket import BucketStorage as _BucketStorage
import apyfal.exceptions as _exc
import apyfal._utilities.aws as _utl_aws


class _ExceptionHandler(_utl_aws.ExceptionHandler):
    """Handle AWS S3 Exceptions.

    Raises:
        apyfal.exceptions.StorageResourceNotExistsException:
            404 error, key not found on bucket.
        apyfal.exceptions.StorageRuntimeException:
            _Storage runtime exception.
    """
    RUNTIME = _exc.StorageRuntimeException
    ERROR_CODE = {'404': _exc.StorageResourceNotExistsException}


class AWSStorage(_BucketStorage):
    """AWS S3 Bucket

    apyfal.storage URL: "AWS.BucketName://ObjectKey"

    Args:
        storage_type (str): Cloud service provider name. Default to "AWS".
        config (str or apyfal.configuration.Configuration): Configuration file path or instance.
            If not set, will search it in current working directory, in current
            user "home" folder. If none found, will use default configuration values.
        client_id (str): AWS Access Key ID.
        secret_id (str): AWS Secret Access Key.
        region (str): AWS region.
        bucket_name (str): Name on the bucket on AWS S3.
    """
    #: Provider name
    NAME = 'AWS'

    #: AWS Website
    DOC_URL = "https://aws.amazon.com"

    def __init__(self, **kwargs):
        _BucketStorage.__init__(self, **kwargs)

        # Load session
        self._session = _boto3.session.Session(
            aws_access_key_id=self._client_id,
            aws_secret_access_key=self._secret_id,
            region_name=self._region
        )

    def _get_bucket(self):
        """Return S3 Bucket

        Returns:
            Bucket object"""
        s3_resource = self._session.resource('s3')
        return s3_resource.Bucket(self._bucket_name)

    def copy_to_local(self, source, local_path):
        """
        Copy a file from storage to local.

        Args:
            source (str): Source URL.
            local_path (str): Local destination path.
        """
        with _ExceptionHandler.catch():
            self._get_bucket().download_file(source, local_path)

    def copy_from_local(self, local_path, destination):
        """
        Copy a file to storage from local.

        Args:
            local_path (str): Local source path.
            destination (str): Destination URL
        """
        with _ExceptionHandler.catch():
            self._get_bucket().upload_file(local_path, destination)

    def copy_to_stream(self, source, stream):
        """
        Copy a file from storage to binary stream.

        Args:
            source (str): Source URL.
            stream (file-like object): Destination binary stream.
        """
        with _ExceptionHandler.catch():
            self._get_bucket().download_fileobj(source, stream)

    def copy_from_stream(self, stream, destination):
        """
        Copy a file to storage from binary stream.

        Args:
            stream (file-like object): Source binary stream.
            destination (str): Destination URL.
        """
        with _ExceptionHandler.catch():
            self._get_bucket().upload_fileobj(stream, destination)

    def _copy_from_aws(self, storage, source, destination):
        """
        Copy from another AWS S3 bucket to this other.

        Args:
            storage (AWSStorage): Other bucket.
            source (str): Source key in other bucket.
            destination (str): Destination key in this bucket.
        """
        with _ExceptionHandler.catch():
            self._get_bucket().copy(
                {'Bucket': storage.bucket, 'Key': source}, destination)
