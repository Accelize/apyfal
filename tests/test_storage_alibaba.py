# coding=utf-8
"""apyfal.storage.oss tests"""

import pytest
from tests.test_storage import (
    run_full_real_test_sequence, import_from_generic_test)


def test_ossclass_import():
    """OSSStorage import"""
    # Test: Import by factory without errors
    import_from_generic_test('Alibaba')


@pytest.mark.need_csp
@pytest.mark.need_csp_alibaba
def test_ossclass_real(tmpdir):
    """OSSStorage in real case"""
    run_full_real_test_sequence('Alibaba', tmpdir)
