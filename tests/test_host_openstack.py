# coding=utf-8
"""apyfal.host.openstack tests"""

import pytest


def test_exception_handler():
    """Tests ExceptionHandler"""
    import keystoneauth1.exceptions.http as _keystoneauth_exceptions
    from openstack.exceptions import SDKException
    from apyfal.host.openstack import _ExceptionHandler
    import apyfal.exceptions as exc

    # Tests no exception
    with _ExceptionHandler.catch():
        assert 1

    # Tests catch authentication exception
    with pytest.raises(exc.HostAuthenticationException):
        with _ExceptionHandler.catch():
            raise _keystoneauth_exceptions.Unauthorized

    # Tests catch other exception
    with pytest.raises(exc.HostRuntimeException):
        with _ExceptionHandler.catch():
            raise SDKException

    # Tests ignore exception
    with _ExceptionHandler.catch(ignore=True):
        raise SDKException
