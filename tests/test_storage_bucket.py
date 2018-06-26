# coding=utf-8
"""apyfal.storage._bucket tests"""

try:
    # Python 2
    from StringIO import StringIO as BytesIO
except ImportError:
    # Python 3
    from io import BytesIO

from shutil import copyfileobj
import uuid

import pytest


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


def import_from_generic_test(storage_type, **kwargs):
    """
    Test to import a class from generic.

    Args:
        storage_type( str): Bucket storage_type
        kwargs: Other args required
    """
    from apyfal.storage import Storage
    Storage(
        storage_type=storage_type, region='dummy_region',
        client_id='dummy_client_id', secret_id='dummy_secret_id',
        **kwargs)


def run_full_real_test_sequence(storage_type, tmpdir):
    """Run common real tests for all buckets.

    Args:
        host_type (str): Bucket storage_type.
        tmpdir (object): tmpdir Pytest fixture
    """
    from apyfal.configuration import Configuration

    # Skip if no correct configuration with this host_type
    config = Configuration()
    full_storage_type = ''
    for section in config:
        if section.lower().startswith(
                'storage.%s.' % storage_type.lower()):
            full_storage_type = section.split('.', 1)[1]

    if not full_storage_type:
        pytest.skip('No configuration for %s.' % storage_type)

    # Initializes local file source
    content = 'dummy_content'.encode()
    tmp_src = tmpdir.join('src.txt')
    tmp_src_path = str(tmp_src)
    tmp_src.write(content)
    assert tmp_src.check(file=True)

    # Initializes local file destination
    tmp_dst = tmpdir.join('dst.txt')
    tmp_dst_path = str(tmp_dst)

    # Initialize storage
    from apyfal.storage import copy, register, _STORAGE, Storage
    _STORAGE.clear()

    # Mock other storage class
    class DummyStorage(Storage):

        def __init__(self, *args, **kwargs):
            """Init storage and create stream"""
            Storage.__init__(self, *args, **kwargs)
            self.stream = BytesIO()
            self.storage_to_storage = False

        def copy_from_stream(self, stream, destination):
            """Write to storage stream from other stream"""
            self.stream = BytesIO()
            copyfileobj(stream, self.stream)
            self.stream.seek(0)

        def copy_to_stream(self, source, stream):
            """Write in stream fro storage stream"""
            self.stream.seek(0)
            copyfileobj(self.stream, stream)

    _STORAGE['dummy'] = DummyStorage('dummy')

    # Tests
    try:
        # Register bucket
        storage = register(full_storage_type)
        storage_dir = '%s://apyfal_testing/' % storage.storage_id

        # Local file to bucket
        file_name = storage_dir + str(uuid.uuid4())
        copy(tmp_src_path, file_name)

        # Bucket to local file
        assert not tmp_dst.check(file=True)
        copy(file_name, tmp_dst_path)
        assert tmp_dst.check(file=True)
        assert tmp_dst.read_binary() == content

        # Storage to bucket
        copy(tmp_src_path, 'dummy://path')
        assert _STORAGE['dummy'].stream.read() == content
        _STORAGE['dummy'].stream.seek(0)

        file_name = storage_dir + str(uuid.uuid4())
        copy('dummy://path', file_name)

        # Bucket to storage
        copy(file_name, 'dummy://path')
        _STORAGE['dummy'].stream.seek(0)
        assert _STORAGE['dummy'].stream.read() == content

        # Bucket to bucket
        file_name2 = storage_dir + str(uuid.uuid4())
        copy(file_name, file_name2)

    # Clear storage
    finally:
        _STORAGE.clear()

        # TODO: Bucket clean up...
