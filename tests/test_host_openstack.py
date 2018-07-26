# coding=utf-8
"""apyfal.host.openstack tests"""

import pytest


def test_exception_handler():
    """Tests ExceptionHandler"""
    from novaclient.exceptions import ClientException, Unauthorized
    from apyfal.host.openstack import _exception_handler
    import apyfal.exceptions as exc

    # Tests no exception
    with _exception_handler():
        assert 1

    # Tests catch authentication exception
    with pytest.raises(exc.HostAuthenticationException):
        with _exception_handler():
            raise Unauthorized('Error')

    # Tests catch other exception
    with pytest.raises(exc.HostRuntimeException):
        with _exception_handler():
            raise ClientException('Error')

    # Tests ignore exception
    with _exception_handler(ignore=True):
        raise ClientException('Error')
