# coding=utf-8
"""apyfal.storage tests"""

from io import BytesIO
from shutil import copyfileobj


def test_storage_hook():
    """Tests _StorageHook"""
    import apyfal.storage as srg

    # Mock Storage
    dummy_storage_type = 'dummy_storage_type'
    dummy_parameters = {}

    class DummyStorage:

        storage_id = dummy_storage_type

        def __init__(self, storage_type=None, **parameters):
            assert storage_type == dummy_storage_type
            assert parameters == dummy_parameters

    srg_storage = srg.Storage
    srg.Storage = DummyStorage

    # Tests
    try:
        # Lazy instanatiation of storage
        hook = srg._StorageHook()
        assert dummy_storage_type not in hook

        storage = hook[dummy_storage_type]
        assert storage.storage_id == dummy_storage_type
        assert dummy_storage_type in hook

        # Manual instantiation
        hook = srg._StorageHook()
        assert dummy_storage_type not in hook

        storage = hook.register(dummy_storage_type, **dummy_parameters)
        assert storage.storage_id == dummy_storage_type
        assert dummy_storage_type in hook

        # Public register function
        srg._STORAGE.clear()
        srg.register(dummy_storage_type, **dummy_parameters)
        assert dummy_storage_type in srg._STORAGE
        assert srg._STORAGE[dummy_storage_type].storage_id == dummy_storage_type

    # Restore Storage
    finally:
        srg.Storage = srg_storage
        srg._STORAGE.clear()


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

    # Tests HTTP
    assert parse_url('http://www.accelize.com') == (
        'http', 'http://www.accelize.com')
    assert parse_url('https://www.accelize.com') == (
        'http', 'https://www.accelize.com')

    # Tests custom storage scheme
    assert parse_url('storage.name://path/on/storage') == (
        'storage.name', 'path/on/storage')


def test_open(tmpdir):
    """Tests open"""
    import apyfal.storage as srg

    srg._STORAGE.clear()
    content = 'dummy_content'.encode()

    # Mock other storage class
    class DummyStorage(srg.Storage):

        def __init__(self, *args, **kwargs):
            """Init storage and create stream"""
            srg.Storage.__init__(self, *args, **kwargs)
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

    srg._STORAGE['dummy'] = storage = DummyStorage('dummy')

    # Tests
    try:
        # Local file
        local_file = tmpdir.join('file.txt')
        local_file.write(content)
        with srg.open(str(local_file), 'rb') as data:
            assert data.read() == content

        with srg.open(str(local_file), 'rt') as data:
            assert data.read() == content.decode()

        # Python 2 unicode URL
        with srg.open(str(local_file).decode(), 'rt') as data:
            assert data.read() == content.decode()

        # Stream:
        stream_file = BytesIO(content)
        with srg.open(stream_file, 'rb') as data:
            assert data.read() == content

        stream_file = BytesIO(content)
        with srg.open(stream_file, 'rt') as data:
            assert data.read() == content.decode()

        # Storage
        with srg.open('dummy://path', 'wb') as data:
            data.write(content)
        assert storage.stream.read() == content

        storage.stream = BytesIO()
        with srg.open('dummy://path', 'wt') as data:
            data.write(content.decode())
        storage.stream.seek(0)
        assert storage.stream.read() == content

        storage.stream.seek(0)
        with srg.open('dummy://path', 'rb') as data:
            assert data.read() == content

        storage.stream.seek(0)
        with srg.open('dummy://path', 'rt') as data:
            assert data.read() == content.decode()

    # Clear registered storage
    finally:
        srg._STORAGE.clear()


def test_copy(tmpdir):
    """Tests copy"""
    from apyfal.storage import copy, _STORAGE, Storage

    # Initializes local file source
    content = 'dummy_content'.encode()
    tmp_src = tmpdir.join('src.txt')
    tmp_src_path = str(tmp_src)
    tmp_src.write(content)
    assert tmp_src.check(file=True)

    # Initializes local file destination
    tmp_dst = tmpdir.join('dst.txt')
    tmp_dst_path = str(tmp_dst)

    # Register a dummy storage
    storage_path = 'path'

    class DummyStorage(Storage):

        def __init__(self, *args, **kwargs):
            """Init storage and create stream"""
            Storage.__init__(self, *args, **kwargs)
            self.stream = BytesIO()
            self.storage_to_storage = False

        def copy_from_stream(self, stream, destination):
            """Write to storage stream from other stream"""
            assert destination == storage_path
            self.stream = BytesIO()
            copyfileobj(stream, self.stream)
            self.stream.seek(0)

        def copy_to_stream(self, source, stream):
            """Write in stream fro storage stream"""
            assert source == storage_path
            self.stream.seek(0)
            copyfileobj(self.stream, stream)

        def _copy_from_dummy(self, storage, source, destination):
            """Copy between 2 storages"""
            assert source == storage_path
            assert destination == storage_path

            storage.stream.seek(0)
            self.stream.seek(0)

            copyfileobj(storage.stream, self.stream)

            storage.stream.seek(0)
            self.stream.seek(0)

            self.storage_to_storage = True

    _STORAGE.clear()
    _STORAGE['dummy1'] = DummyStorage('dummy1')
    _STORAGE['dummy2'] = DummyStorage('dummy2')

    # Tests
    try:
        # Local to local
        assert not tmp_dst.check(file=True)
        copy(tmp_src_path, tmp_dst_path)
        assert tmp_dst.check(file=True)
        assert tmp_dst.read_binary() == content
        tmp_dst.remove()

        # Local to local with scheme
        assert not tmp_dst.check(file=True)
        copy('file://%s' % tmp_src_path, 'file://%s' % tmp_dst_path)
        assert tmp_dst.check(file=True)
        assert tmp_dst.read_binary() == content
        tmp_dst.remove()

        # Local to storage
        assert not _STORAGE['dummy1'].stream.read()
        copy(tmp_src_path, 'dummy1://path')
        assert _STORAGE['dummy1'].stream.read() == content

        # Storage to local
        assert not tmp_dst.check(file=True)
        copy('dummy1://path', tmp_dst_path)
        assert tmp_dst.check(file=True)
        assert tmp_dst.read_binary() == content
        tmp_dst.remove()

        # Stream to stream
        src_stream = BytesIO(content)
        dst_stream = BytesIO()
        copy(src_stream, dst_stream)
        dst_stream.seek(0)
        assert dst_stream.read() == content

        # Stream to local
        assert not tmp_dst.check(file=True)
        src_stream.seek(0)
        copy(src_stream, tmp_dst_path)
        assert tmp_dst.check(file=True)
        assert tmp_dst.read_binary() == content
        tmp_dst.remove()

        # Local to stream
        dst_stream = BytesIO()
        copy(tmp_src_path, dst_stream)
        dst_stream.seek(0)
        assert dst_stream.read() == content

        # Stream to storage
        src_stream.seek(0)
        assert not _STORAGE['dummy2'].stream.read()
        copy(src_stream, 'dummy2://path')
        assert _STORAGE['dummy2'].stream.read() == content

        # Storage to stream
        dst_stream = BytesIO()
        copy('dummy1://path', dst_stream)
        dst_stream.seek(0)
        assert dst_stream.read() == content

        # Storage to storage (Using temporary file)
        _STORAGE['dummy1'].NAME = None
        _STORAGE['dummy2'].stream = BytesIO()
        assert not _STORAGE['dummy2'].stream.read()
        copy('dummy1://path', 'dummy2://path')
        assert _STORAGE['dummy2'].stream.read() == content
        assert not _STORAGE['dummy1'].storage_to_storage
        assert not _STORAGE['dummy2'].storage_to_storage

        # Storage to storage (Using special method)
        _STORAGE['dummy1'].NAME = 'dummy'
        _STORAGE['dummy2'].NAME = 'dummy'
        _STORAGE['dummy2'].stream = BytesIO()
        assert not _STORAGE['dummy2'].stream.read()
        assert not _STORAGE['dummy2'].storage_to_storage
        copy('dummy1://path', 'dummy2://path')
        assert _STORAGE['dummy2'].storage_to_storage
        assert _STORAGE['dummy2'].stream.read() == content

    # Clear registered storage
    finally:
        _STORAGE.clear()


def test_storage():
    """Tests Storage"""
    from apyfal.storage import Storage

    # Tests subclass instantiation
    storage = Storage('http')
    assert storage.NAME == 'HTTP'
    assert storage.storage_id == 'http'
