# coding=utf-8
"""apyfal.storage.ovh tests"""

import pytest
from tests.test_storage_bucket import run_full_real_test_sequence, import_from_generic_test


def test_ovhclass_import():
    """OVHStorage import"""
    # Test: Import by factory without errors
    import_from_generic_test('OVH', project_id='dummy_project')


@pytest.mark.need_csp
@pytest.mark.need_csp_ovh
def test_awsclass_real(tmpdir):
    """OVHStorage in real case"""
    run_full_real_test_sequence('OVH', tmpdir)
