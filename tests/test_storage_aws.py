# coding=utf-8
"""apyfal.storage.aws tests"""

import pytest
from tests.test_storage import (
    run_full_real_test_sequence, import_from_generic_test)


def test_s3class_import():
    """S3Storage import"""
    # Test: Import by factory without errors
    import_from_generic_test('AWS')


@pytest.mark.need_csp
@pytest.mark.need_csp_aws
def test_s3class_real(tmpdir):
    """S3Storage in real case"""
    run_full_real_test_sequence('AWS', tmpdir)
