# coding=utf-8
"""apyfal.client.rest tests"""
import io
import json

import pytest
import requests


def test_restclient_is_alive():
    """Tests RESTClient.is_alive"""
    from apyfal.client.rest import RESTClient
    from apyfal.exceptions import ClientRuntimeException

    # Mock some client parts
    class Client(RESTClient):
        """Dummy AcceleratorClient"""

        def __init__(self, host_ip=None):
            """Do not initialize"""
            self._url = host_ip

        def __del__(self):
            """Do nothing"""

    # Test: No host
    client = Client()
    with pytest.raises(ClientRuntimeException):
        client._is_alive()

    # Test: URL exists
    client = Client(
        host_ip='https://www.accelize.com')
    client._is_alive()

    # Test: URL not exist
    client = Client(
        host_ip='https://www.url_that_not_exists.accelize.com')
    with pytest.raises(ClientRuntimeException):
        client._is_alive()


def test_restclient_url():
    """Tests RESTClient.url"""
    from apyfal.client.rest import RESTClient
    from apyfal.exceptions import ClientConfigurationException

    # Mock some client parts
    class Client(RESTClient):
        """Dummy AcceleratorClient"""
        use_last_configuration_called = False

        def __del__(self):
            """Does nothing"""

        def _use_last_configuration(self):
            """Checks if called"""
            self.use_last_configuration_called = True

    accelerator = Client('Dummy')

    # Test: No accelerator provided
    with pytest.raises(ClientConfigurationException):
        Client()

    # Test: No URL provided
    with pytest.raises(ClientConfigurationException):
        accelerator.url = None

    with pytest.raises(ClientConfigurationException):
        accelerator.url = ''

    # Test: Invalid URL provided
    # Not for test all bad URL cases, only that check_url
    # function is properly called
    with pytest.raises(ValueError):
        accelerator.url = 'http://url_not_valid'

    # Test: Valid URL
    ip_address = '127.0.0.1'
    url = 'http://%s' % ip_address
    accelerator.url = url
    assert accelerator._url == url
    assert accelerator.use_last_configuration_called
    for key in accelerator._REST_API:
        assert accelerator._endpoints[key] == url + accelerator._REST_API[key]

    # Test: URL set with IP
    accelerator.url = ip_address
    assert accelerator._url == url


def test_restclient_start():
    """Tests RESTClient.start"""
    from apyfal.client.rest import RESTClient

    dummy_id = 123
    dummy_url = 'https://www.accelize.com'
    parameters_result = {'app': {'status': 0}}
    response_json = json.dumps({
        'id': dummy_id, 'parametersresult': parameters_result,
        'url': dummy_url, 'inerror': False}).encode()
    file_content = b'content'
    file_in = io.BytesIO(file_content)

    # Mock some client parts

    class Client(RESTClient):
        """Dummy AcceleratorClient"""

        def __del__(self):
            """Does nothing"""

        def _use_last_configuration(self):
            """Does nothing"""

    client = Client('accelerator', host_ip=dummy_url)

    # Mocks requests session
    class Session(requests.Session):
        """Fake requests.Session"""

        @staticmethod
        def get(url, **_):
            """Checks input arguments and returns fake response"""
            # Checks input parameters
            assert '/configuration/%s' % dummy_id in url

            # Returns fake response
            response = requests.Response()
            response._content = response_json
            response.status_code = 200
            return response

        @staticmethod
        def post(url, data=None, **_):
            """Checks input arguments and returns fake response"""
            # Checks input parameters
            assert '/configuration' in url
            stream = data.fields['datafile'][1]
            stream.seek(0)
            assert stream.read() == file_content
            assert json.loads(data.fields['parameters']) == (
                client._configuration_parameters)

            # Returns fake response
            response = requests.Response()
            response._content = response_json
            response.status_code = 200
            return response

    client._session = Session()

    # Test: new configuration
    assert client.start(datafile=file_in, info_dict=True)

    # Test: Already configured
    assert not client.start(info_dict=True)


def test_restclient_use_last_configuration():
    """Tests RESTClient._use_last_configuration"""
    from apyfal.client.rest import RESTClient

    response_json = None
    url = 'https://www.accelize.com'

    # Mocks client and requests session

    class Client(RESTClient):
        """Dummy AcceleratorClient"""

        def __del__(self):
            """Does nothing"""

    class Session(requests.Session):
        """Fake requests.Session"""

        @staticmethod
        def get(url, **_):
            """Checks input arguments and returns fake response"""
            # Checks input parameters
            assert '/configuration' in url

            # Returns fake response
            response = requests.Response()
            response._content = response_json
            return response

    client = Client('accelerator')
    client._session = Session()
    client.url = url
    assert not client._configuration_url

    # Test: Invalid response
    response_json = b''
    client._use_last_configuration()
    assert not client._configuration_url

    response_json = json.dumps({}).encode()
    client._use_last_configuration()
    assert not client._configuration_url

    # Test: No previous configuration
    response_json = json.dumps({'results': []}).encode()
    client._use_last_configuration()
    assert not client._configuration_url

    # Test: Unused configuration
    response_json = json.dumps({'results': [{'used': 0, 'url': url}]}).encode()
    client._use_last_configuration()
    assert not client._configuration_url

    # Test: Valid configuration
    response_json = json.dumps({'results': [{'used': 1, 'url': url}]}).encode()
    client._use_last_configuration()
    assert client._configuration_url == url


def test_restclient_stop():
    """Tests RESTClient.stop"""
    from apyfal.client.rest import RESTClient
    from apyfal.exceptions import ClientRuntimeException

    # Mock OpenApi REST API StopApi
    is_alive = True
    response_dict = {'app': {'status': 0, 'msg': ''}}
    response_json = json.dumps(response_dict).encode()

    class Session(requests.Session):
        """Fake requests.Session"""

        @staticmethod
        def get(url, **_):
            """Checks input arguments and returns fake response"""
            # Checks input parameters
            assert '/stop' in url

            # Returns fake response
            response = requests.Response()
            response._content = response_json
            return response

    # Mock some accelerators parts
    class Client(RESTClient):
        """Dummy AcceleratorClient"""

        def __init__(self, *args, **kwargs):
            RESTClient.__init__(self, *args, **kwargs)
            self._session = Session()
            self._url = 'https://www.accelize.com'

        def _is_alive(self):
            """Raise on demand"""
            if not is_alive:
                raise ClientRuntimeException()

    # Test: AcceleratorClient to stop
    client = Client('Dummy')
    assert not client._stopped
    assert client.stop(info_dict=True) == response_dict
    assert client._stopped

    # Test: Auto-stops with context manager
    with Client('Dummy') as client:
        assert not client._stopped
    assert client._stopped

    # Test: No accelerator to stop
    is_alive = False
    assert Client('Dummy').stop(info_dict=True) is None


def test_restclient_process():
    """Tests RESTClient._process"""
    import apyfal.exceptions as exc
    from apyfal.client.rest import RESTClient

    dummy_id = 123
    dummy_url = 'https://www.accelize.com'
    datafileresult = 'url/to/file'
    parameters_result = {'app': {'status': 0}}
    response_json = json.dumps({
        'id': dummy_id, 'parametersresult': parameters_result,
        'datafileresult': datafileresult, 'processed': True,
        'url': dummy_url, 'inerror': False}).encode()
    file_content = b'content'
    file_in = io.BytesIO(file_content)
    file_out = io.BytesIO()

    # Mock some client parts

    class Client(RESTClient):
        """Dummy AcceleratorClient"""

        def __del__(self):
            """Does nothing"""

        def _use_last_configuration(self):
            """Does nothing"""

    client = Client('accelerator', host_ip=dummy_url)

    # Mocks requests session
    class Session(requests.Session):
        """Fake requests.Session"""

        @staticmethod
        def get(url, **_):
            """Checks input arguments and returns fake response"""
            response = requests.Response()
            response.status_code = 200

            if '/process/%s' % dummy_id in url:
                response._content = response_json
            elif url == datafileresult:
                response.raw = io.BytesIO(file_content)
                response.raw.seek(0)
            else:
                raise ValueError('Unexpected url: %s' % url)

            return response

        @staticmethod
        def post(url, data=None, **_):
            """Checks input arguments and returns fake response"""
            # Checks input parameters
            assert '/process' in url
            stream = data.fields['datafile'][1]
            stream.seek(0)
            assert data.fields['configuration'] == dummy_url
            assert stream.read() == file_content
            assert json.loads(data.fields['parameters']) == (
                client._process_parameters)

            # Returns fake response
            response = requests.Response()
            response._content = response_json
            response.status_code = 200
            return response

        @staticmethod
        def delete(url, data=None, **_):
            """Checks input arguments and returns fake response"""
            # Checks input parameters
            assert '/process/%s' % dummy_id in url in url

    client._session = Session()

    # Test: No configuration
    with pytest.raises(exc.ClientConfigurationException):
        assert client.process(file_in=file_in)
    client._configuration_url = dummy_url

    # Test: run process
    client.process(file_in=file_in, file_out=file_out)
    file_out.seek(0)
    assert file_out.read() == file_content


def test_restclient_raise_for_error():
    """Tests RESTClient._raise_for_error"""
    from apyfal.client.rest import RESTClient
    import apyfal.exceptions as exc

    response = requests.Response()

    # Test: Everything OK
    response_dict = {'inerror': False}
    response._content = json.dumps(response_dict).encode()
    response.status_code = 200
    assert RESTClient._raise_for_error(response) == response_dict

    # Test: HTTP Error
    response.status_code = 500
    with pytest.raises(exc.ClientRuntimeException):
        RESTClient._raise_for_error(response)

    # Test: Invalid response
    response.status_code = 200
    response._content = b''
    with pytest.raises(exc.ClientRuntimeException):
        RESTClient._raise_for_error(response)

    # Test: in error response
    response._content = json.dumps({'inerror': True}).encode()
    with pytest.raises(exc.ClientRuntimeException):
        RESTClient._raise_for_error(response)

    # Test: No in error in response
    response._content = json.dumps({}).encode()
    with pytest.raises(exc.ClientRuntimeException):
        RESTClient._raise_for_error(response)
