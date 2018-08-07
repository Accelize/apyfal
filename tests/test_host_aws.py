# coding=utf-8
"""apyfal.host.aws tests"""

import pytest
from tests.test_host_csp import run_full_real_test_sequence, \
    import_from_generic_test


def test_exception_handler():
    """Tests ExceptionHandler"""
    from botocore.exceptions import ClientError
    from apyfal.host.aws import _exception_handler
    import apyfal.exceptions as exc

    response = {'Error': {'Code': 'ErrorCode', 'Message': 'Error'}}

    # Tests no exception
    with _exception_handler():
        assert 1

    # Tests catch specified exception
    with pytest.raises(exc.HostRuntimeException):
        with _exception_handler(to_catch=ValueError):
            raise ValueError

    # Tests raises specified exception
    with pytest.raises(exc.HostConfigurationException):
        with _exception_handler(
                to_raise=exc.HostConfigurationException):
            raise ClientError(response, 'testing')

    # Tests ignore error code
    with _exception_handler(filter_error_codes='ErrorCode'):
        raise ClientError(response, 'testing')

    # Tests other error code
    with pytest.raises(exc.HostRuntimeException):
        with _exception_handler():
            raise ClientError(response, 'testing')


def test_awsclass_import():
    """AWSHost import"""
    # Test: Import by factory without errors
    import_from_generic_test('AWS')


@pytest.mark.need_csp
@pytest.mark.need_csp_aws
def test_awsclass_real():
    """AWSHost in real case"""
    run_full_real_test_sequence('AWS', {
        'eu-west-1': {
            # Image name: ubuntu-xenial-16.04-amd64-server-20180522
            'image': 'ami-58d7e821',
            'instancetype': 't2.nano',
            'fpgaimage': 'None'
        }})
