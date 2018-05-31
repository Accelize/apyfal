# coding=utf-8
"""acceleratorAPI.ovh tests"""

import pytest
from tests.test_csp___init__ import run_full_real_test_sequence, import_from_generic_test


def test_ovhclass_import():
    """OVHClass import"""
    # Test: Import by factory without errors
    import_from_generic_test('OVH', project_id='dummy_project')


@pytest.mark.need_csp
@pytest.mark.need_csp_ovh
def test_ovhclass_real():
    """OVHClass in real case"""
    # Test: Full generic sequence
    run_full_real_test_sequence('OVH', {
        'GRA3': {
            # Image name: Debian 9
            'image': 'b1ad5a98-e83f-45f3-a60e-5a9fea01d141',
            'instancetype': 's1-2'
        }}, support_stop_restart=False)
