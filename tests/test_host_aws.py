# coding=utf-8
"""apyfal.host.aws tests"""

import pytest
from tests.test_host_generic_csp import run_full_real_test_sequence, import_from_generic_test


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