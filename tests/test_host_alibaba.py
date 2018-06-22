# coding=utf-8
"""apyfal.host.aws tests"""

import json

import pytest
from tests.test_host_csp import run_full_real_test_sequence, import_from_generic_test


def test_alibibaclass_import():
    """AlibabaHost import"""
    # Test: Import by factory without errors
    import_from_generic_test('Alibaba')


def test_alibibaclass_request():
    """AlibabaHost._request"""
    import apyfal.host.alibaba as alibaba
    from apyfal.host.alibaba import AlibabaCSP
    import apyfal.exceptions as exc
    from aliyunsdkcore import client
    from aliyunsdkcore.acs_exception.exceptions import ServerException

    # Mocks some variables
    client_id = 'dummy_access_key'
    secret_id = 'dummy_secret_key'
    region = 'dummy_region_id'
    action = 'DummyAction'
    parameters = {'DummyString': 'dummy_value',
                  'DummyNumber': 0,
                  'DummyList': ['dummy_value']}
    response = {'DummyResponse': 0}
    raises_exception = []
    status_desc = 'testing'

    # Mocks client
    class DummyAcsClient:

        def __init__(self, ak, secret, region_id):
            """Checks parameters"""
            assert ak == client_id
            assert secret == secret_id
            assert region_id == region

        @staticmethod
        def do_action_with_exception(acs_request):
            """Checks parameters returns fake response and
            raise exceptions"""
            # Checks request
            assert acs_request.get_action_name() == action
            acs_request_params = acs_request.get_query_params()
            for param in parameters:
                assert param in acs_request_params
                assert isinstance(acs_request_params[param], str)
            assert 'ClientToken' in acs_request_params
            assert acs_request.get_protocol_type() == "https"

            # Raises fake exceptions
            if raises_exception:
                raise ServerException(*raises_exception)

            # Returns fake response
            return json.dumps(response)

    client_acs_client = client.AcsClient
    client.AcsClient = DummyAcsClient
    alibaba._AcsClient = DummyAcsClient

    # Tests
    try:
        csp = AlibabaCSP(client_id=client_id, secret_id=secret_id, region=region)

        # Everything OK
        assert csp._request(action, **parameters) == response

        # Raise exception
        raises_exception = ['DummyCode', 'dummy_message']
        with pytest.raises(exc.HostRuntimeException) as exc_info:
            csp._request(action, **parameters)
            for part in raises_exception:
                assert part in exc_info

        raises_exception[0] = 'InvalidParameter'
        with pytest.raises(exc.HostConfigurationException):
            csp._request(action, **parameters)

        raises_exception[0] = 'InvalidAccessKey'
        with pytest.raises(exc.HostAuthenticationException):
            csp._request(action, **parameters)

        # Filter codes
        raises_exception[0] = 'DummyCode'
        with pytest.raises(ServerException):
            csp._request(action, error_code_filter='DummyCode', **parameters)

        with pytest.raises(ServerException):
            csp._request(action, error_code_filter=(
                'DummyCode', 'AnotherCode'), **parameters)

        # Test "_instance_request"
        raises_exception = []
        assert csp._instance_request(action, **parameters) == response

        # Tests "_instance_request" timeout if instance with incorrect status
        raises_exception = ['IncorrectInstanceStatus', 'dummy_message']
        parameters['InstanceId'] = 'dummy_instance_id'
        csp.TIMEOUT = 0.0
        with pytest.raises(exc.HostRuntimeException) as exc_info:
            csp._instance_request(action, status_desc=status_desc, **parameters)
            assert status_desc in exc_info

        # Tests "_instance_request" stills throw other exceptions
        raises_exception[0] = 'DummyCode'
        with pytest.raises(exc.HostRuntimeException) as exc_info:
            csp._instance_request(action, status_desc=status_desc, **parameters)
            for part in raises_exception:
                assert part in exc_info

    # Restore AcsClient
    finally:
        client.AcsClient = client_acs_client
        alibaba._AcsClient = client_acs_client

@pytest.mark.need_csp
@pytest.mark.need_csp_alibaba
def test_alibabaclass_real():
    """AlibabaHost in real case"""
    run_full_real_test_sequence('Alibaba', {
        'cn-hangzhou': {
            # Image name: Debian 8.9 64bit / 20Go HDD
            'image': 'debian_8_09_64_20G_alibase_20170824.vhd',
            'instancetype': 'ecs.t5-lc2m1.nano',
        }})
