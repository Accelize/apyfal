# coding=utf-8
"""Alibaba Cloud OSS"""
from contextlib import contextmanager as _contextmanager
from shutil import copyfileobj as _copyfileobj

import oss2 as _oss

import apyfal.exceptions as _exc
from apyfal.storage._bucket import BucketStorage as _BucketStorage


@_contextmanager
def _exception_handler():
    """Handle OSS exceptions"""
    # Performs Operation
    try:
        yield

    # Raises Apyfal Exception based on OSS error status
    except _oss.exceptions.OssError as exception:
        raise {404: _exc.StorageResourceNotExistsException,
               403: _exc.StorageAuthenticationException}.get(
                    exception.status, _exc.StorageRuntimeException
                    )(exc='%s: %s' % (exception.code, exception.message))


class OSSStorage(_BucketStorage):
    """Alibaba Cloud OSS Bucket

    apyfal.storage URL: "oss://BucketName/ObjectKey"

    Args:
        storage_type (str): Cloud service provider name. Default to "Alibaba".
        config (str or apyfal.configuration.Configuration or file-like object):
            Can be Configuration instance, apyfal.storage URL, paths, file-like object.
            If not set, will search it in current working directory, in current
            user "home" folder. If none found, will use default configuration values.
        client_id (str): Alibaba Access Key ID.
        secret_id (str): Alibaba Secret Access Key.
        region (str): Alibaba region.
    """
    #: Service name
    NAME = 'OSS'

    #: Provider name
    HOST_NAME = 'Alibaba'

    #: Alibaba Website
    DOC_URL = 'https://www.alibabacloud.com'

    def __init__(self, region=None, **kwargs):
        _BucketStorage.__init__(self, **kwargs)

        self._region = self._from_config('region', region)

    def _get_bucket(self, path):
        """
        Get bucket and file path from global path.

        Args:
            path (str): path

        Returns:
            tuple: bucket, file path
        """
        bucket_name, path = path.split('/', 1)
        with _exception_handler():
            bucket = _oss.Bucket(
                _oss.Auth(self._client_id, self._secret_id),
                'http://oss-%s.aliyuncs.com' % self._region,
                bucket_name)
        return bucket, path

    def copy_to_local(self, source, local_path):
        """
        Copy a file from storage to local.

        Args:
            source (str): Source URL.
            local_path (str): Local destination path.
        """
        bucket, path = self._get_bucket(source)
        with _exception_handler():
            bucket.get_object_to_file(path, local_path)

    def copy_from_local(self, local_path, destination):
        """
        Copy a file to storage from local.

        Args:
            local_path (str): Local source path.
            destination (str): Destination URL
        """
        bucket, path = self._get_bucket(destination)
        with _exception_handler():
            bucket.put_object_from_file(path, local_path)

    def copy_to_stream(self, source, stream):
        """
        Copy a file from storage to binary stream.

        Args:
            source (str): Source URL.
            stream (file-like object): Destination binary stream.
        """
        bucket, path = self._get_bucket(source)
        with _exception_handler():
            _copyfileobj(bucket.get_object(path), stream)

    def copy_from_stream(self, stream, destination):
        """
        Copy a file to storage from binary stream.

        Args:
            stream (file-like object): Source binary stream.
            destination (str): Destination URL.
        """
        bucket, path = self._get_bucket(destination)
        with _exception_handler():
            bucket.put_object(path, stream)
