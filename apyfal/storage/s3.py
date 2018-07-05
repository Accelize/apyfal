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


class S3Storage(_BucketStorage):
    """AWS S3 Bucket

    apyfal.storage URL: s3://BucketName/ObjectKey

    Args:
        storage_type (str): Cloud service provider name. Default to "AWS".
        config (str or apyfal.configuration.Configuration or file-like object):
            Can be Configuration instance, apyfal.storage URL, paths, file-like object.
            If not set, will search it in current working directory, in current
            user "home" folder. If none found, will use default configuration values.
        client_id (str): AWS Access Key ID.
        secret_id (str): AWS Secret Access Key.
    """
    #: Service name
    NAME = 'S3'

    #: Provider name
    HOST_NAME = 'AWS'

    #: AWS Website
    DOC_URL = "https://aws.amazon.com"

    def __init__(self, **kwargs):
        _BucketStorage.__init__(self, **kwargs)

        # Load session
        self._session = _boto3.session.Session(
            aws_access_key_id=self._client_id,
            aws_secret_access_key=self._secret_id,
        )

    def _get_bucket(self, path):
        """
        Get bucket and file path from global path.

        Args:
            path (str): path

        Returns:
            tuple: bucket, file path
        """
        bucket_name, path = path.split('/', 1)
        with _ExceptionHandler.catch():
            bucket = self._session.resource('s3').Bucket(bucket_name)
        return bucket, path

    def copy_to_local(self, source, local_path):
        """
        Copy a file from storage to local.

        Args:
            source (str): Source URL.
            local_path (str): Local destination path.
        """
        bucket, path = self._get_bucket(source)
        with _ExceptionHandler.catch():
            bucket.download_file(path, local_path)

    def copy_from_local(self, local_path, destination):
        """
        Copy a file to storage from local.

        Args:
            local_path (str): Local source path.
            destination (str): Destination URL
        """
        bucket, path = self._get_bucket(destination)
        with _ExceptionHandler.catch():
            bucket.upload_file(local_path, path)

    def copy_to_stream(self, source, stream):
        """
        Copy a file from storage to binary stream.

        Args:
            source (str): Source URL.
            stream (file-like object): Destination binary stream.
        """
        bucket, path = self._get_bucket(source)
        with _ExceptionHandler.catch():
            bucket.download_fileobj(source, stream)

    def copy_from_stream(self, stream, destination):
        """
        Copy a file to storage from binary stream.

        Args:
            stream (file-like object): Source binary stream.
            destination (str): Destination URL.
        """
        bucket, path = self._get_bucket(destination)
        with _ExceptionHandler.catch():
            bucket.upload_fileobj(stream, destination)

    def _copy_from_aws(self, source, destination):
        """
        Copy from another AWS S3 bucket to this other.

        Args:
            source (str): Source key in other bucket.
            destination (str): Destination key in this bucket.
        """
        dst_bucket, dst_path = self._get_bucket(destination)
        src_bucket, src_path = source.split('/', 1)
        with _ExceptionHandler.catch():
            dst_bucket.copy(
                {'Bucket': src_bucket, 'Key': src_path}, dst_path)
