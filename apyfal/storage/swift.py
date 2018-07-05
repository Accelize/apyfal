# coding=utf-8
"""OpenStack Swift"""
# Absolute import required on Python 2 to avoid collision
# of this module with openstack-sdk package
from __future__ import absolute_import as _absolute_import

import openstack as _openstack

from apyfal.storage._bucket import BucketStorage as _BucketStorage
import apyfal.exceptions as _exc
import apyfal._utilities.openstack as _utl_openstack


class _ExceptionHandler(_utl_openstack.ExceptionHandler):
    """Host OpenStack exception handler"""
    RUNTIME = _exc.StorageRuntimeException
    AUTHENTICATION = _exc.StorageAuthenticationException


class SwiftStorage(_BucketStorage):
    """OpenStack Swift Object Storage

    apyfal.storage URL: "swift://ContainerName/ObjectName"

    Args:
        storage_type (str): Cloud service provider name. Default to "OpenStack".
        config (str or apyfal.configuration.Configuration or file-like object):
            Can be Configuration instance, apyfal.storage URL, paths, file-like object.
            If not set, will search it in current working directory, in current
            user "home" folder. If none found, will use default configuration values.
        client_id (str): OpenStack Access Key ID.
        secret_id (str): OpenStack Secret Access Key.
        region (str): OpenStack region.
        project_id (str): OpenStack Project
        auth_url (str): OpenStack auth-URL
        interface (str): OpenStack interface
    """
    #: Service name
    NAME = 'Swift'

    #: Provider name
    HOST_NAME = 'OpenStack'

    # Default OpenStack auth-URL to use (str)
    OPENSTACK_AUTH_URL = None

    # Default Interface to use (str)
    OPENSTACK_INTERFACE = None

    def __init__(self, region=None, project_id=None, auth_url=None, interface=None, **kwargs):
        _BucketStorage.__init__(self, **kwargs)

        # Read configuration
        self._region = self._from_config('region', region)
        self._project_id = self._from_config('project_id', project_id)
        self._auth_url = (
            self._from_config('auth_url', auth_url) or
            self.OPENSTACK_AUTH_URL)
        self._interface = (
            self._from_config('interface', interface) or
            self.OPENSTACK_INTERFACE)

        # Load session
        self._session = _utl_openstack.connect(
            region=self._region, auth_url=self._auth_url,
            client_id=self._client_id, secret_id=self._secret_id,
            project_id=self._project_id, interface=self._interface)

    def copy_to_stream(self, source, stream):
        """
        Copy a file from storage to binary stream.

        Args:
            source (str): Source URL.
            stream (file-like object): Destination binary stream.
        """
        container, path = self._get_bucket(source)
        with _ExceptionHandler.catch(
                to_catch=_openstack.exceptions.NotFoundException,
                to_raise=_exc.StorageResourceNotExistsException):
            data = self._session.object_store.download_object(
                path, container=container)
        stream.write(data)

    def copy_from_stream(self, stream, destination):
        """
        Copy a file to storage from binary stream.

        Args:
            stream (file-like object): Source binary stream.
            destination (str): Destination URL.
        """
        container, path = self._get_bucket(destination)
        data = stream.read()
        with _ExceptionHandler.catch():
            self._session.object_store.create_object(
                container=container, name=path, data=data)
