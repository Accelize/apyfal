# coding=utf-8
"""apyfal.storage.aws tests"""

import pytest
from tests.test_storage_bucket import run_full_real_test_sequence, import_from_generic_test


def test_awsclass_import():
    """AWSStorage import"""
    # Test: Import by factory without errors
    import_from_generic_test('AWS')


def test_handle_s3_exception():
    """Tests _handle_s3_exception"""
    from botocore.exceptions import ClientError
    from apyfal.storage.aws import _handle_s3_exception
    import apyfal.exceptions as exc

    # Tests no exception
    with _handle_s3_exception():
        assert 1

    # Tests 404 error code
    response = {'Error': {'Code': '404'}}

    with pytest.raises(exc.StorageResourceNotExistsException):
        with _handle_s3_exception():
            raise ClientError(response, 'testing')

    # Tests other error code
    response['Error']['Code'] = '300'
    with pytest.raises(exc.StorageRuntimeException):
        with _handle_s3_exception():
            raise ClientError(response, 'testing')


@pytest.mark.need_csp
@pytest.mark.need_csp_aws
def test_awsclass_real(tmpdir):
    """AWSStorage in real case"""
    run_full_real_test_sequence('AWS', tmpdir)
