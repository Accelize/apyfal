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


class AlibabaStorage(_BucketStorage):
    """Alibaba Cloud OSS Bucket

    apyfal.storage URL: "Alibaba.BucketName://ObjectKey"

    Args:
        storage_type (str): Cloud service provider name. Default to "Alibaba".
        config (str or apyfal.configuration.Configuration or file-like object):
            Can be Configuration instance, apyfal.storage URL, paths, file-like object.
            If not set, will search it in current working directory, in current
            user "home" folder. If none found, will use default configuration values.
        client_id (str): Alibaba Access Key ID.
        secret_id (str): Alibaba Secret Access Key.
        region (str): Alibaba region.
        bucket_name (str): Name on the bucket on Alibaba Cloud OSS.
    """
    #: Provider name
    NAME = "Alibaba"

    #: Alibaba Website
    DOC_URL = 'https://www.alibabacloud.com'

    def _get_bucket(self):
        """Get OSS bucket

        Returns:
            objct: OSS bucket object.
        """
        return _oss.Bucket(
            _oss.Auth(self._client_id, self._secret_id),
            'http://oss-%s.aliyuncs.com' % self._region,
            self._bucket_name)

    def copy_to_local(self, source, local_path):
        """
        Copy a file from storage to local.

        Args:
            source (str): Source URL.
            local_path (str): Local destination path.
        """
        with _exception_handler():
            self._get_bucket().get_object_to_file(
                source, local_path)

    def copy_from_local(self, local_path, destination):
        """
        Copy a file to storage from local.

        Args:
            local_path (str): Local source path.
            destination (str): Destination URL
        """
        with _exception_handler():
            self._get_bucket().put_object_from_file(
                destination, local_path)

    def copy_to_stream(self, source, stream):
        """
        Copy a file from storage to binary stream.

        Args:
            source (str): Source URL.
            stream (file-like object): Destination binary stream.
        """
        with _exception_handler():
            _copyfileobj(self._get_bucket().get_object(source), stream)

    def copy_from_stream(self, stream, destination):
        """
        Copy a file to storage from binary stream.

        Args:
            stream (file-like object): Source binary stream.
            destination (str): Destination URL.
        """
        with _exception_handler():
            self._get_bucket().put_object(destination, stream)
