# coding=utf-8
"""apyfal.ovh tests"""

import pytest
from tests.test_host_csp import run_full_real_test_sequence, \
    import_from_generic_test


def test_ovhclass_import():
    """OVHHost import"""
    # Test: Import by factory without errors
    import_from_generic_test('OVH', project_id='dummy_project')


@pytest.mark.need_csp
@pytest.mark.need_csp_ovh
def test_ovhclass_real():
    """OVHHost in real case"""
    # Test: Full generic sequence
    run_full_real_test_sequence('OVH', {
        'GRA3': {
            # Image name: Debian 9
            'image': '805fec88-c545-40cc-a1c2-e44c890450e6',
            'instancetype': 's1-2'
        }})
