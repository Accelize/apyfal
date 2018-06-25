# coding=utf-8
"""apyfal.storage._bucket tests"""


def test_storage_bucket_storage():
    """Tests BucketStorage"""
    from apyfal.storage._bucket import BucketStorage

    # Mock subclass
    class DummyBucket(BucketStorage):

        NAME = 'dummy'

        def copy_to_stream(self, *_):
            """Do nothing"""

        def copy_from_stream(self, *_):
            """Do nothing"""

    # Test: Instantiation
    bucket = DummyBucket(storage_type='dummy.bucket')
    assert bucket._storage_type == 'dummy'
    assert bucket.storage_id == 'dummy.bucket'
    assert bucket.bucket == 'bucket'

    bucket = DummyBucket(storage_type='dummy', bucket_name='bucket')
    assert bucket._storage_type == 'dummy'
    assert bucket.storage_id == 'dummy.bucket'
    assert bucket.bucket == 'bucket'
