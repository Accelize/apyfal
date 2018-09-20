# coding=utf-8
"""apyfal._utilities tests"""
import os
import time

import requests

import pytest


def test_timeout():
    """Tests Timeout"""
    from apyfal._utilities import Timeout

    # Should not timeout
    with Timeout(timeout=1, sleep=0.001) as timeout:
        while True:
            assert not timeout.reached()
            break

    # Should timeout
    with Timeout(timeout=0.0) as timeout:
        while True:
            time.sleep(0.1)
            assert timeout.reached()
            break


def test_get_host_public_ip():
    """Tests get_host_public_ip"""
    from apyfal._utilities import get_host_public_ip
    import ipgetter
    from random import randint

    random = False

    # Mock ipgetter.myip
    def dummy_myip():
        """Return fake IP"""
        if random:
            return '%d.%d.%d.%d' % (
                randint(0, 255),
                randint(0, 255),
                randint(0, 255),
                randint(0, 255)
            )
        return '127.0.0.1'

    ipgetter_myip = ipgetter.myip
    ipgetter.myip = dummy_myip

    # Test
    try:
        # Check format
        assert get_host_public_ip() == '127.0.0.1/32'

        # Raise errors if no returns
        random = True
        with pytest.raises(OSError):
            get_host_public_ip()

    # Restore ipgetter.myip
    finally:
        ipgetter.myip = ipgetter_myip

    # Test with ipgetter.myip directly
    # May fail if no connection
    try:
        assert get_host_public_ip()[-3:] == '/32'
    except OSError:
        # May fail on some CI
        pytest.xfail('Unable to get public IP address')


def test_create_key_pair_file(tmpdir):
    """Tests create_key_pair_file"""
    from apyfal._utilities import create_key_pair_file
    import apyfal._utilities as _utl

    tmp_dir = tmpdir.dirpath()
    ssh_dir = tmp_dir.join('.ssh')
    key_pair = 'key_pair'
    key_content = 'key_content'

    # Mock SSH path
    utl_ssh_dir = _utl.SSH_DIR
    _utl.SSH_DIR = str(ssh_dir)

    # Tests
    try:
        assert not ssh_dir.check(dir=True)

        # Not existing file
        create_key_pair_file(key_pair, key_content)
        assert ssh_dir.check(dir=True)
        assert ssh_dir.join(key_pair + '.pem').check(file=True)
        assert ssh_dir.join(key_pair + '.pem').read('rt') == key_content

        # File with same content exists
        create_key_pair_file(key_pair, key_content)
        assert not ssh_dir.join(key_pair + '_2.pem').check(file=True)

        # File with different content exists
        key_content = 'another_key_content'
        create_key_pair_file(key_pair, key_content)
        assert ssh_dir.join(key_pair + '_2.pem').check(file=True)
        assert ssh_dir.join(key_pair + '_2.pem').read('rt') == key_content

    # Restore os.path.expanduser
    finally:
        _utl.SSH_DIR = utl_ssh_dir


def test_recursive_update():
    """Tests test_recursive_update"""
    from apyfal._utilities import recursive_update

    to_update = {'root1': {'key1': 1, 'key2': 2}, 'key3': 3}
    update = {'root1': {'key1': 1.0, 'key4': 4.0}, 'key5': 5.0}
    expected = {'root1': {'key1': 1.0, 'key2': 2, 'key4': 4.0},
                'key3': 3, 'key5': 5.0}

    assert recursive_update(to_update, update) == expected


def test_handle_request_exceptions():
    """Tests handle_request_exceptions"""
    from apyfal._utilities import handle_request_exceptions
    import apyfal.exceptions as exc

    # Tests no exception
    with handle_request_exceptions(exc.AcceleratorException):
        assert 1

    # Catch exception
    with pytest.raises(exc.AcceleratorException):
        with handle_request_exceptions(exc.AcceleratorException):
            raise requests.RequestException


def test_memoizedmethod():
    """Tests memoizedmethod"""
    from apyfal._utilities import memoizedmethod

    # Tests _memoize
    class Dummy:

        def __init__(self):
            self._cache = {}

        @memoizedmethod
        def to_memoize(self, arg):
            """Fake method"""
            return arg

    dummy = Dummy()
    assert not dummy._cache
    value = 'value'
    assert dummy.to_memoize(value) == value
    assert dummy._cache == {'to_memoize': value}
    assert dummy.to_memoize(value) == value


def test_format_url():
    """Tests format_url"""
    from apyfal._utilities import format_url

    # Test: Empty values
    assert format_url('') is None
    assert format_url(None) is None

    # Test: Values without schemes
    assert format_url('127.0.0.1') == 'http://127.0.0.1'
    assert format_url('localhost') == 'http://localhost'
    assert format_url('accelize.com') == 'http://accelize.com'

    # Test: Values with schemes
    assert format_url('http://127.0.0.1') == 'http://127.0.0.1'
    assert format_url('http://localhost') == 'http://localhost'
    assert format_url('http://accelize.com') == 'http://accelize.com'

    # Test: Bad URL
    with pytest.raises(ValueError):
        format_url('http://accelize')

    # Test: Force HTTPS
    assert format_url('http://accelize.com',
                      force_secure=True) == 'https://accelize.com'
    assert format_url('https://accelize.com',
                      force_secure=True) == 'https://accelize.com'
