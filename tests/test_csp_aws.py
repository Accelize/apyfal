# coding=utf-8
"""acceleratorAPI.csp.aws tests"""

import pytest
from tests.test_csp___init__ import run_full_real_test_sequence, import_from_generic_test


def test_awsclass_import():
    """AWSClass import"""
    # Test: Import by factory without errors
    import_from_generic_test('AWS')


@pytest.mark.need_csp
@pytest.mark.need_csp_aws
def test_awsclass_real():
    """AWSClass in real case"""
    run_full_real_test_sequence('AWS', {
        'eu-west-1': {
            # Image name: ubuntu-xenial-16.04-amd64-server-20180522
            'image': 'ami-58d7e821',
            'instancetype': 't2.nano',
            'fpgaimage': 'None'
        }})
