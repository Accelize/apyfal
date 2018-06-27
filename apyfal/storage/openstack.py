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


class OpenStackStorage(_BucketStorage):
    """OpenStack Object Storage

    apyfal.storage URL: "OpenStack.ContainerName://ObjectName"

    Args:
        storage_type (str): Cloud service provider name. Default to "OpenStack".
        config (str or apyfal.configuration.Configuration): Configuration file path or instance.
            If not set, will search it in current working directory, in current
            user "home" folder. If none found, will use default configuration values.
        client_id (str): OpenStack Access Key ID.
        secret_id (str): OpenStack Secret Access Key.
        region (str): OpenStack region.
        bucket_name (str): Name on the container on OpenStack.
        project_id (str): OpenStack Project
        auth_url (str): OpenStack auth-URL
        interface (str): OpenStack interface
    """
    # TODO: Update all "config" docstring with apyfal.storage
    #: Provider name
    NAME = 'OpenStack'

    # Default OpenStack auth-URL to use (str)
    OPENSTACK_AUTH_URL = None

    # Default Interface to use (str)
    OPENSTACK_INTERFACE = None

    def __init__(self, project_id=None, auth_url=None, interface=None, **kwargs):
        _BucketStorage.__init__(self, **kwargs)

        # Read configuration
        section = self._config['storage.%s' % self.storage_id]
        self._project_id = project_id or section['project_id']
        self._auth_url = (
            auth_url or section['auth_url'] or
            self.OPENSTACK_AUTH_URL)
        self._interface = (
            interface or section['interface'] or
            self.OPENSTACK_INTERFACE)
        # TODO: Check mandatory arguments

        # Load session
        self._session = _openstack.connection.Connection(
            region_name=self._region,
            auth=dict(
                auth_url=self._auth_url,
                username=self._client_id,
                password=self._secret_id,
                project_id=self._project_id
            ),
            compute_api_version='2',
            identity_interface=self._interface
        )

    def copy_to_stream(self, source, stream):
        """
        Copy a file from storage to binary stream.

        Args:
            source (str): Source URL.
            stream (file-like object): Destination binary stream.
        """
        with _ExceptionHandler.catch(
                to_catch=_openstack.exceptions.NotFoundException,
                to_raise=_exc.StorageResourceNotExistsException):
            data = self._session.object_store.download_object(
                source, container=self._bucket_name)
        stream.write(data)

    def copy_from_stream(self, stream, destination):
        """
        Copy a file to storage from binary stream.

        Args:
            stream (file-like object): Source binary stream.
            destination (str): Destination URL.
        """
        data = stream.read()
        with _ExceptionHandler.catch():
            self._session.object_store.create_object(
                container=self._bucket_name, name=destination,
                data=data)
