# coding=utf-8
"""apyfal.storage tests"""
from io import BytesIO
from sys import version_info
from os import urandom

import pytest


def test_mount():
    """Tests mount"""
    import apyfal.storage as srg
    from apyfal.configuration import Configuration
    from apyfal.exceptions import StorageConfigurationException
    import pycosio

    # Mock _Storage and pycosio.mount
    storage_type = 'dummy_storage'
    storage_name = 'dummy_name'
    user = 'dummy_user'
    password = 'dummy_password'
    excepted_storage_parameters = {
            'user': user,
            'arg0': 'arg0',
            'params': {'password': password,
                       'arg1': 'arg1'}}
    mounted = []

    class DummyStorage(srg._Storage):
        """Dummy storage"""
        NAME = storage_type
        STORAGE_NAME = storage_name
        EXTRA_ROOT = 'dummy_mount://'
        STORAGE_PARAMETERS = {
            'user': 'self._client_id',
            'arg0': 'arg0',
            'params': {'password': 'self._secret_id',
                       'arg1': 'arg1'}}

    def mount(storage=None, extra_root=None, storage_parameters=None, **_):
        """Dummy pycosio.mount"""
        assert storage == storage_name
        assert extra_root == DummyStorage.EXTRA_ROOT
        assert storage_parameters == excepted_storage_parameters
        mounted.append(storage)

    pycosio_mount = pycosio.mount
    pycosio.mount = mount

    # Tests
    try:
        # Mount
        assert not mounted
        config = Configuration()
        config['host.%s' % storage_type]['secret_id'] = password
        DummyStorage(config=config, client_id=user).mount()
        assert mounted == [storage_name]

        # Mount with no class available
        if version_info[0] > 2:
            with pytest.raises(StorageConfigurationException):
                srg.mount(storage_type, config=config, client_id=user)

        # SSL option
        assert DummyStorage()._unsecure is False
        assert DummyStorage(unsecure=True)._unsecure is True
        assert DummyStorage(unsecure='True')._unsecure is True
        assert DummyStorage(unsecure=False)._unsecure is False
        assert DummyStorage(unsecure='False')._unsecure is False

    # Restore pycosio
    finally:
        pycosio.mount = pycosio_mount


def test_parse_url():
    """Tests parse_url"""
    from apyfal.storage import parse_url

    # Tests client local file
    assert parse_url('path/without/scheme') == (
        'file', 'path/without/scheme')
    assert parse_url('file://path/with/scheme') == (
        'file', 'path/with/scheme')

    # Tests host local file conversion
    assert parse_url('host://path/on/host') == (
        'file', 'path/on/host')

    # Tests custom storage scheme
    assert parse_url('storage.name://path/on/storage') == (
        'storage.name', 'path/on/storage')


def test_open(tmpdir):
    """Tests open and copy"""
    import apyfal.storage as srg

    # Prepares files
    src_file = tmpdir.join('src.txt')
    dst_file = tmpdir.join('dst.txt')
    content = 'dummy_content'.encode()
    src_file.write(content)

    # Tests open binary stream
    with srg.open(BytesIO(content), 'rb') as opened:
        assert opened.read() == content

    # Tests open text stream
    assert not hasattr(BytesIO(content), 'encoding')
    with srg.open(BytesIO(content), 'rt') as opened:
        assert opened.read() == content.decode()

    # Tests open file
    with srg.open(str(src_file), 'rb') as opened:
        assert opened.read() == content

    # Tests copy file
    srg.copy(str(src_file), str(dst_file))
    assert src_file.read_binary() == dst_file.read_binary()


def import_from_generic_test(storage_type, **kwargs):
    """
    Test to import a class from generic.

    Args:
        storage_type( str): Bucket storage_type
        kwargs: Other args required
    """
    from apyfal.storage import _Storage
    _Storage(
        storage_type=storage_type, region='dummy_region',
        client_id='dummy_client_id', secret_id='dummy_secret_id',
        **kwargs)


def run_full_real_test_sequence(storage_type, tmpdir):
    """Run common real tests for all buckets.

    Args:
        storage_type (str): Bucket storage_type.
        tmpdir (object): tmpdir Pytest fixture
    """
    from apyfal.storage import _Storage, copy, open as srg_open

    # Skip if no correct configuration with this host_type
    if not _Storage(storage_type=storage_type)._client_id:
        pytest.skip('No configuration for %s.' % storage_type)

    # Initializes local file source
    content = urandom(4096)
    tmp_src = tmpdir.join('src.txt')
    tmp_src_path = str(tmp_src)
    tmp_src.write_binary(content)
    assert tmp_src.check(file=True)

    # Initializes local file destination
    tmp_dst = tmpdir.join('dst.txt')
    tmp_dst_path = str(tmp_dst)

    # Mount bucket
    storage = _Storage(storage_type=storage_type)
    storage.EXTRA_ROOT = 'storage://'
    storage.mount()
    storage_dir = ('%stestaccelizestorage/apyfal_testing/' %
                   storage.EXTRA_ROOT)

    # Local file to bucket
    file_name = storage_dir + '001.dat'
    copy(tmp_src_path, file_name)

    # Bucket to local file
    assert not tmp_dst.check(file=True)
    copy(file_name, tmp_dst_path)
    assert tmp_dst.check(file=True)
    assert tmp_dst.read_binary() == content

    # Bucket to bucket
    file_name2 = storage_dir + '002.dat'
    copy(file_name, file_name2)

    # Read with open
    with srg_open(file_name2, 'rb') as file2:
        assert file2.read() == content
