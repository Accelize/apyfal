# coding=utf-8
"""OpenStack utilities"""
# Absolute import required on Python 2 to avoid collision
# of this module with openstack-sdk package
from __future__ import absolute_import

from contextlib import contextmanager

import keystoneauth1.exceptions.http as keystoneauth_exceptions
from openstack.exceptions import SDKException
from openstack.connection import Connection

from apyfal.exceptions import AcceleratorException


class ExceptionHandler:
    """Handler for OpenStack exceptions."""
    # Needs to be overridden with exceptions to re-raises
    RUNTIME = AcceleratorException
    AUTHENTICATION = AcceleratorException

    @classmethod
    @contextmanager
    def catch(cls, to_catch=SDKException, to_raise=None, ignore=False, **exc_kwargs):
        """
        Context manager that catch OpenStack exceptions and raises
        Apyfal exceptions.

        Args:
            to_catch (Exception or tuple of Exception): Exception to catch.
                SDKException if not specified.
            to_raise (apyfal.exception.AcceleratorException subclass):
                Exception to raise. self.RUNTIME if not specified.
            ignore (bool): If True, don't raises exception.
            exc_kwargs: Exception to raise arguments.
        """
        # Performs operation
        try:
            yield

        # Catch authentication exceptions
        except keystoneauth_exceptions.Unauthorized as exception:
            raise cls.AUTHENTICATION(exc=exception)

        # Catch specified exceptions
        except to_catch as exception:
            # Raises Apyfal exception
            if not ignore:
                raise (to_raise or cls.RUNTIME)(exc=exception, **exc_kwargs)


def connect(region, auth_url, client_id, secret_id, project_id, interface):
    """
    Connect to OpenStack.

    Args:
        region (str): OpenStack region.
        auth_url (str): OpenStack auth_url.
        client_id (str): OpenStack client ID.
        secret_id (str): OpenStack secret ID.
        project_id (str): OpenStack project ID.
        interface (str): OpenStack interface.

    Returns:
        Connection: OpenStack connection.
    """
    return Connection(
        region_name=region,
        auth=dict(
            auth_url=auth_url, username=client_id,
            password=secret_id, project_id=project_id),
        compute_api_version='2', identity_interface=interface)
