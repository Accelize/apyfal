# coding=utf-8
"""acceleratorAPI.ovh tests"""

import pytest
from tests.test_csp___init__ import run_full_real_test_sequence


def test_ovhclass_import():
    """OVHClass import"""
    # Test: Import by factory without errors
    from acceleratorAPI.csp import CSPGenericClass
    CSPGenericClass(provider='OVH', region='dummy_region')


@pytest.mark.need_csp
@pytest.mark.need_csp_ovh
def test_ovhclass_real():
    """OVHClass in real case"""
    # Test: Full generic sequence
    run_full_real_test_sequence('OVH', {
        'GRA3': {
            'image': 'Debian 9',
            'instancetype': 's1-2'
        }})
