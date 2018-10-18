# coding=utf-8
"""apyfal.client.rest tests"""
from copy import deepcopy
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

        def __del__(self):
            """Does nothing"""

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
    for key in accelerator._REST_API:
        assert accelerator._endpoints[key] == url + accelerator._REST_API[key]

    # Test: URL set with IP
    accelerator.url = ip_address
    assert accelerator._url == url


def test_restclient_start(tmpdir):
    """Tests RESTClient.start"""
    import apyfal
    from apyfal.client.rest import RESTClient
    from apyfal._certificates import self_signed_certificate
    import apyfal.configuration as _cfg

    dummy_id = 123
    dummy_url_https = 'https://www.accelize.com'
    dummy_url_http = 'http://www.accelize.com'
    parameters_result = {'app': {'status': 0}}
    response_json = json.dumps({
        'id': dummy_id, 'parametersresult': parameters_result,
        'url': dummy_url_https, 'inerror': False}).encode()
    file_content = b'content'
    src = io.BytesIO(file_content)
    has_src = True

    # Mock some client parts

    class Client(RESTClient):
        """Dummy AcceleratorClient"""

        def __del__(self):
            """Does nothing"""

    client = Client('accelerator', host_ip=dummy_url_https,
                    accelize_client_id='client', accelize_secret_id='secret')

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
            if has_src:
                stream = data.fields['datafile'][1]
                stream.seek(0)
                assert stream.read() == file_content
            else:
                assert 'datafile' not in data.fields
            excepted = deepcopy(client._configuration_parameters)
            excepted['app']['reset'] = True
            excepted['app']['reload'] = True
            excepted['env']['apyfal_version'] = apyfal.__version__
            assert json.loads(data.fields['parameters']) == excepted

            # Returns fake response
            response = requests.Response()
            response._content = response_json
            response.status_code = 200
            return response

    client._cache['_session'] = Session()

    # Test: new configuration
    info_dict = dict()
    assert client.start(
        src=src, info_dict=info_dict, reset=True, reload=True) is None
    assert info_dict

    # Test "datafile" backward compatibility
    info_dict.clear()
    assert client.start(
        datafile=src, info_dict=info_dict, reset=True, reload=True) is None
    assert info_dict

    # Test no input file
    info_dict.clear()
    has_src = False
    assert client.start(info_dict=info_dict, reset=True, reload=True) is None
    assert info_dict
    has_src = True

    # Test: stream SSL Certificate, with DNS and wildcard name
    for address in ("accelize.com", "*"):
        ssl_crt_bytes = self_signed_certificate(
            address, common_name='host_name', country_name='FR')[0]
        ssl_cert_crt = io.BytesIO(ssl_crt_bytes)
        client = Client('accelerator', host_ip=dummy_url_https,
                        accelize_client_id='client', accelize_secret_id='secret',
                        ssl_cert_crt=ssl_cert_crt)
        assert client.ssl_cert_crt == ssl_cert_crt
        assert client.url == dummy_url_https
        with open(client._session.verify, 'rb') as tmp_cert:
            assert tmp_cert.read() == ssl_crt_bytes

    # Test: File SSL Certificate
    ssl_cert_crt_file = tmpdir.join('certificate.crt')
    ssl_cert_crt_file.write(ssl_crt_bytes)
    ssl_cert_crt = str(ssl_cert_crt_file)
    client = Client('accelerator', host_ip=dummy_url_http,
                    accelize_client_id='client', accelize_secret_id='secret',
                    ssl_cert_crt=str(ssl_cert_crt))
    assert client.ssl_cert_crt == ssl_cert_crt
    assert client._session.verify == ssl_cert_crt
    assert client.url == dummy_url_https

    # Test: Generated SSL Certificate
    ssl_cert_crt_file = tmpdir.join('certificate_generated.crt')
    ssl_cert_crt_file.write(ssl_crt_bytes)
    ssl_cert_crt = str(ssl_cert_crt_file)
    cfg_apyfal_cert_crt = _cfg.APYFAL_CERT_CRT
    _cfg.APYFAL_CERT_CRT = ssl_cert_crt
    try:
        client = Client(
            'accelerator', host_ip=dummy_url_http,
            accelize_client_id='client', accelize_secret_id='secret')
        assert client.ssl_cert_crt is None
        assert client._session.verify == ssl_cert_crt
        assert client.ssl_cert_crt == ssl_cert_crt
        assert client.url == dummy_url_https

        # Tests: Disabled generated certificate
        client = Client(
            'accelerator', host_ip=dummy_url_http,
            accelize_client_id='client', accelize_secret_id='secret',
            ssl_cert_crt=False)
        assert client.ssl_cert_crt is False
        assert client._session.verify is True
        assert client.ssl_cert_crt is False
        assert client.url == dummy_url_http

    finally:
        _cfg.APYFAL_CERT_CRT = cfg_apyfal_cert_crt


def test_restclient_configuration_url():
    """Tests RESTClient._configuration_url"""
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
        def get(request_url, **_):
            """Checks input arguments and returns fake response"""
            # Checks input parameters
            assert '/configuration' in request_url

            # Returns fake response
            response = requests.Response()
            response._content = response_json
            return response

    client = Client('accelerator')
    client._cache['_session'] = Session()
    client.url = url
    assert not client._configuration_url

    # Test: Invalid response
    response_json = b''
    assert not client._configuration_url

    response_json = json.dumps({}).encode()
    del client._cache['_configuration_url']
    assert not client._configuration_url

    # Test: No previous configuration
    response_json = json.dumps({'results': []}).encode()
    del client._cache['_configuration_url']
    assert not client._configuration_url

    # Test: Unused configuration
    response_json = json.dumps({'results': [{'used': 0, 'url': url}]}).encode()
    del client._cache['_configuration_url']
    assert not client._configuration_url

    # Test: Valid configuration
    response_json = json.dumps({'results': [{'used': 1, 'url': url}]}).encode()
    del client._cache['_configuration_url']
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
            self._cache['_session'] = Session()
            self._url = 'https://www.accelize.com'

            self.call__stop = False
            self.call_stop = False

        def _is_alive(self):
            """Raise on demand"""
            if not is_alive:
                raise ClientRuntimeException()

        def _stop(self, *arg, **kwargs):
            """Mark as called"""
            self.call__stop = True
            return RESTClient._stop(self, *arg, **kwargs)

        def stop(self, *arg, **kwargs):
            """Mark as called"""
            self.call_stop = True
            return RESTClient.stop(self, *arg, **kwargs)

    # Test: AcceleratorClient to stop
    client = Client('Dummy')
    assert not client.call__stop
    info_dict = dict()
    assert client.stop(info_dict=info_dict) is None
    assert client.call__stop
    assert info_dict == response_dict

    # Test: no info dict
    client = Client('Dummy')
    assert not client.call__stop
    assert client.stop() is None
    assert client.call__stop

    # Test: Auto-stops with context manager
    with Client('Dummy') as client:
        assert not client.call__stop
        assert not client.call_stop
    assert client.call_stop
    assert not client.call__stop

    with Client('Dummy') as client:
        client._stopped = True
        assert not client.call__stop
        assert not client.call_stop
    assert not client.call_stop
    assert not client.call__stop

    # Test: No accelerator to stop
    is_alive = False
    info_dict.clear()
    assert Client('Dummy').stop(info_dict=info_dict) is None
    assert not info_dict


def test_restclient_process():
    """Tests RESTClient._process"""
    import apyfal.exceptions as exc
    from apyfal.client.rest import RESTClient

    dummy_id = 123
    dummy_url = 'https://www.accelize.com'
    datafileresult = 'url/to/file'
    parameters_result = {'app': {'status': 0}}
    response_dict = {
        'id': dummy_id, 'parametersresult': parameters_result,
        'datafileresult': datafileresult, 'processed': True,
        'url': dummy_url, 'inerror': False}
    response_json = json.dumps(response_dict).encode()
    response_dict['processed'] = False
    response_json_not_ready = json.dumps(response_dict).encode()
    file_content = b'content'
    src = io.BytesIO(file_content)
    dst = io.BytesIO()
    has_src = True
    processed_retry = [0]

    # Mock some client parts

    class Client(RESTClient):
        """Dummy AcceleratorClient"""

        def __del__(self):
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

            if ('/process/%s' % dummy_id) in url:
                # Simulate processing not completed
                if processed_retry[0] < 2:
                    response._content = response_json_not_ready
                    processed_retry[0] += 1
                else:
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
            if has_src:
                stream = data.fields['datafile'][1]
                stream.seek(0)
                assert stream.read() == file_content
            else:
                assert 'datafile' not in data.fields
            assert data.fields['configuration'] == dummy_url
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

    client._cache['_session'] = Session()
    client._cache["_configuration_url"] = None

    # Test: No configuration
    with pytest.raises(exc.ClientConfigurationException):
        assert client.process(src=src)
    client._cache["_configuration_url"] = dummy_url

    # Test: run process
    client.process(src=src, dst=dst)
    dst.seek(0)
    assert dst.read() == file_content

    # Test: file_in/file_out backward compatibility
    dst.seek(0)
    client.process(file_in=src, file_out=dst)
    dst.seek(0)
    assert dst.read() == file_content

    # Test: No Input
    has_src = False
    dst.seek(0)
    client.process(file_out=dst)
    dst.seek(0)
    assert dst.read() == file_content
    has_src = True

    # Test: No Output
    dst.seek(0)
    client.process(file_in=src)
    assert dst.tell() == 0

    # Test: run process with info_dict
    dst.seek(0)
    info_dict = dict()
    assert client.process(src=src, dst=dst, info_dict=info_dict) is None
    assert info_dict == parameters_result
    dst.seek(0)
    assert dst.read() == file_content


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
