# coding=utf-8
"""OpenStack utilities"""
# Absolute import required on Python 2 to avoid collision
# of this module with openstack-sdk package
from __future__ import absolute_import

from contextlib import contextmanager

import keystoneauth1.exceptions.http as _keystoneauth_exceptions
from openstack.exceptions import SDKException


class ExceptionHandler:
    """Handler for OpenStack exceptions."""
    # Needs to be overridden with exceptions to re-raises
    RUNTIME = None
    AUTHENTICATION = None

    @classmethod
    @contextmanager
    def catch(cls, catch_exc=SDKException, exc_type=None, ignore=False, **kwargs):
        """Context manager that catch OpenStack exceptions and raises
        Apyfal exceptions.

        Args:
            catch_exc (Exception): Exception to catch.
                SDKException if not specified.
            exc_type (apyfal.exception.AcceleratorException subclass):
                Exception to raise. self.RUNTIME if not specified.
            ignore (bool): If True, don't raises exception."""
        # Performs operation in with
        try:
            yield

        # Catch authentication exceptions
        except _keystoneauth_exceptions.Unauthorized as exception:
            raise cls.AUTHENTICATION(exc=exception)

        # Catch specified exceptions
        except catch_exc as exception:
            # Raises Apyfal exception
            if not ignore:
                raise (exc_type or cls.RUNTIME)(exc=exception, **kwargs)

        # TODO: Improve error message handling.
