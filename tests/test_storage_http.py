# coding=utf-8
"""apyfal.storage.http tests"""

try:
    # Python 2
    from StringIO import StringIO as BytesIO
except ImportError:
    # Python 3
    from io import BytesIO

import requests


def test_storage_http():
    """Tests HTTPStorage"""
    from apyfal.storage.http import HTTPStorage

    # Mocks requests in utilities

    dummy_url = 'http://www.accelize.com'
    content = 'dummy_content'.encode()

    class GetResponse:
        """Fake requests.Response"""

        raw = BytesIO(content)

        @staticmethod
        def raise_for_status():
            """Do nothing"""

    class PostResponse:
        """Fake requests.Response"""

        @staticmethod
        def raise_for_status():
            """Do nothing"""

    class DummySession(requests.Session):
        """Fake requests.Session"""

        @staticmethod
        def get(url, **_):
            """Checks input arguments and returns fake response"""
            # Checks input arguments
            assert url == dummy_url

            # Returns fake response
            return GetResponse()

        @staticmethod
        def post(url, data=None, **_):
            """Checks input arguments and returns fake response"""
            # Checks input arguments
            assert url == dummy_url
            data.seek(0)
            assert data.read() == content

            # Returns fake response
            return PostResponse()

    # Monkey patch requests in utilities
    requests_session = requests.Session
    requests.Session = DummySession

    # Tests
    try:
        storage = HTTPStorage()

        # Read
        stream = BytesIO()
        storage.copy_to_stream(dummy_url, stream)
        stream.seek(0)
        assert stream.read() == content
        stream.seek(0)

        # Write
        storage.copy_from_stream(stream, dummy_url)

    # Restore requests
    finally:
        requests.Session = requests_session
