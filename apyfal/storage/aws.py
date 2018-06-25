# coding=utf-8
"""Amazon Web Services S3"""

from contextlib import contextmanager as _contextmanager

import boto3 as _boto3
import botocore.exceptions as _boto_exceptions

from apyfal.storage._bucket import BucketStorage as _BucketStorage
import apyfal.exceptions as _exc


@_contextmanager
def _handle_s3_exception(bucket_key=None):
    """Handle Boto exceptions and raise Apyfal exception

    Args:
        bucket_key (str): Bucket key accessed

    Raises:
        apyfal.exceptions.StorageResourceNotExistsException:
            404 error, key not found on bucket.
        apyfal.exceptions.StorageRuntimeException:
            _Storage runtime exception.
    """
    try:
        yield
    except _boto_exceptions.ClientError as exception:
        if exception.response['Error']['Code'] == "404":
            raise _exc.StorageResourceNotExistsException(
                exc=bucket_key)
        else:
            raise _exc.StorageRuntimeException(
                exc=exception)


class AWSStorage(_BucketStorage):
    """AWS S3 Bucket

    apyfal.storage.copy URL: "AWS.BucketName://KeyToObject"

    Args:
        host_type (str): Cloud service provider name. Default to "AWS".
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

    @property
    def client(self):
        """AWS client managing bucket.

        Returns:
            object: Boto3 client."""
        return self._session

    def copy_to_local(self, source, local_path):
        """
        Copy a file from storage to local.

        Args:
            source (str): Source URL.
            local_path (str): Local destination path.
        """
        with _handle_s3_exception(source):
            self._get_bucket().download_file(source, local_path)

    def copy_from_local(self, local_path, destination):
        """
        Copy a file to storage from local.

        Args:
            local_path (str): Local source path.
            destination (str): Destination URL
        """
        with _handle_s3_exception():
            self._get_bucket().upload_file(local_path, destination)

    def copy_to_stream(self, source, stream):
        """
        Copy a file from storage to binary stream.

        Args:
            source (str): Source URL.
            stream (file-like object): Destination binary stream.
        """
        with _handle_s3_exception(source):
            self._get_bucket().download_fileobj(source, stream)

    def copy_from_stream(self, stream, destination):
        """
        Copy a file to storage from binary stream.

        Args:
            stream (file-like object): Source binary stream.
            destination (str): Destination URL.
        """
        with _handle_s3_exception():
            self._get_bucket().upload_fileobj(stream, destination)

    def _copy_from_aws(self, storage, source, destination):
        """
        Copy from another AWS S3 bucket to this other.

        Args:
            storage (AWSStorage): Other bucket.
            source (str): Source key in other bucket.
            destination (str): Destination key in this bucket.
        """
        with _handle_s3_exception(source):
            self._get_bucket().copy(
                {'Bucket': storage.bucket, 'Key': source},
                destination, SourceClient=storage.client)
