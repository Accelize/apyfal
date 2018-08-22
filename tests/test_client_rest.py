# coding=utf-8
"""apyfal.client.rest tests"""
import collections
from contextlib import contextmanager
import copy
import io
import gc
import json
import sys

import pytest
import requests


def test_restclient_is_alive():
    """Tests RESTClient.is_alive"""
    from apyfal.client.rest import RESTClient
    from apyfal.exceptions import ClientRuntimeException

    # Mock some accelerators parts
    class DummyAccelerator(RESTClient):
        """Dummy AcceleratorClient"""

        def __init__(self, host_ip=None):
            """Do not initialize"""
            self._url = host_ip

        def __del__(self):
            """Do nothing"""

    # Test: No host
    client = DummyAccelerator()
    with pytest.raises(ClientRuntimeException):
        client._is_alive()

    # Test: URL exists
    client = DummyAccelerator(
        host_ip='https://www.accelize.com')
    client._is_alive()

    # Test: URL not exist
    client = DummyAccelerator(
        host_ip='https://www.url_that_not_exists.accelize.com')
    with pytest.raises(ClientRuntimeException):
        client._is_alive()


def test_restclient_url():
    """Tests RESTClient.url"""
    from apyfal.client.rest import RESTClient
    from apyfal.exceptions import ClientConfigurationException

    # Mock some accelerators parts
    class DummyAccelerator(RESTClient):
        """Dummy AcceleratorClient"""
        use_last_configuration_called = False

        def __del__(self):
            """Does nothing"""

        def _use_last_configuration(self):
            """Checks if called"""
            self.use_last_configuration_called = True

    accelerator = DummyAccelerator('Dummy')

    # Test: No accelerator provided
    with pytest.raises(ClientConfigurationException):
        DummyAccelerator()

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
    assert accelerator._api_client.configuration.host == url
    assert accelerator.use_last_configuration_called

    # Test: URL set with IP
    accelerator.url = ip_address
    assert accelerator._url == url


def test_restclient_start():
    """Tests RESTClient.start"""
    from apyfal.client.rest import RESTClient
    from apyfal.exceptions import ClientRuntimeException
    import apyfal.client.rest._openapi as rest_api

    # Mock OpenApi REST API ConfigurationApi
    excepted_parameters = None
    excepted_datafile = None
    configuration_read_in_error = 0

    base_parameters_result = {
        'app': {'status': 0, 'msg': 'dummy_msg'}}

    class ConfigurationApi:
        """Fake rest_api.ConfigurationApi"""

        def __init__(self, api_client):
            """Store API client"""
            self.api_client = api_client

        @staticmethod
        def configuration_create(parameters, datafile):
            """Checks input arguments and returns fake response"""

            # Check parameters
            if excepted_parameters is not None:
                assert json.loads(parameters) == excepted_parameters
            if excepted_datafile is not None:
                assert datafile == excepted_datafile

            # Return response
            Response = collections.namedtuple(
                'Response', ['url', 'id', 'parametersresult'])

            return Response(
                url='dummy_url', id='dummy_id',
                parametersresult=json.dumps(base_parameters_result))

        @staticmethod
        def configuration_read(id_value):
            """Checks input arguments and returns fake response"""
            Response = collections.namedtuple('Response',
                                              ['inerror', 'id', 'url'])

            # Check parameters
            assert id_value == 'dummy_id'

            # Return response
            return Response(url='dummy_url', id=id_value,
                            inerror=configuration_read_in_error)

    # Mock some accelerators parts
    class DummyAccelerator(RESTClient):
        """Dummy AcceleratorClient"""

        def __del__(self):
            """Does nothing"""

        @staticmethod
        @contextmanager
        def _data_file(url, *_, **__):
            """Skip file presence check"""
            yield url

        @property
        def url(self):
            """Fake URL"""
            return 'dummy_accelerator_url'

    client_id = 'dummy_client_id'
    secret_id = 'dummy_secret_id'

    accelerator = DummyAccelerator(
        'Dummy', accelize_client_id=client_id,
        accelize_secret_id=secret_id)

    base_parameters = {
        "env": {
            "client_id": client_id,
            "client_secret": secret_id}}

    base_response = {'url_config': 'dummy_url',
                     'url_instance': accelerator.url}

    # Monkey patch OpenAPI client with mocked API
    rest_api_configuration_api = rest_api.ConfigurationApi
    rest_api.ConfigurationApi = ConfigurationApi

    # Tests
    try:
        # Check with arguments
        accelerator_parameters = {'dummy_param': None}
        excepted_parameters = base_parameters.copy()
        excepted_parameters.update(accelerator._configuration_parameters)
        excepted_parameters['app']['specific'] = accelerator_parameters
        excepted_datafile = 'dummy_datafile'
        excepted_response = base_response.copy()
        excepted_response.update(base_parameters_result)

        assert excepted_response == accelerator.start(
            datafile=excepted_datafile, info_dict=True,
            **accelerator_parameters)

        # Check default values
        excepted_datafile = ''
        excepted_parameters = base_parameters.copy()
        excepted_parameters.update(accelerator._configuration_parameters)
        excepted_response = base_response.copy()
        excepted_response.update(base_parameters_result)

        # On already configured
        assert accelerator.start(info_dict=True) is None

        # On not configured
        accelerator._configuration_url = None
        assert accelerator.start(info_dict=True) == excepted_response

        # Check error from host
        configuration_read_in_error = 1
        accelerator._configuration_url = None
        with pytest.raises(ClientRuntimeException):
            accelerator.start()

    # Restore OpenApi client API
    finally:
        rest_api.ConfigurationApi = rest_api_configuration_api


def test_restclient_use_last_configuration():
    """Tests RESTClient._use_last_configuration"""
    from apyfal.client.rest import RESTClient
    import apyfal.client.rest._openapi as rest_api

    # Mock OpenApi REST API ConfigurationApi
    Config = collections.namedtuple('Config', ['url', 'used'])
    config_list = []
    configuration_list_raises = False

    class ConfigurationApi:
        """Fake rest_api.ConfigurationApi"""

        def __init__(self, api_client):
            """Store API client"""
            self.api_client = api_client

        @staticmethod
        def configuration_list():
            """Returns fake response"""
            if configuration_list_raises:
                raise ValueError
            Response = collections.namedtuple('Response', ['results'])
            return Response(results=config_list)

    # Monkey patch OpenApi client with mocked API
    rest_api_configuration_api = rest_api.ConfigurationApi
    rest_api.ConfigurationApi = ConfigurationApi

    # Tests:
    # method called through AcceleratorClient.url, through AcceleratorClient.__init__
    try:

        # No previous configuration
        accelerator = RESTClient(
            'Dummy', host_ip='https://www.accelize.com')
        assert accelerator._configuration_url is None

        configuration_list_raises = True
        accelerator = RESTClient(
            'Dummy', host_ip='https://www.accelize.com')
        assert accelerator._configuration_url is None
        configuration_list_raises = False

        # Unused previous configuration
        config_list.append(Config(url='dummy_config_url', used=0))
        accelerator = RESTClient(
            'Dummy', host_ip='https://www.accelize.com')
        assert accelerator._configuration_url is None

        # Used previous configuration
        config_list.insert(0, Config(url='dummy_config_url_2', used=1))
        accelerator = RESTClient(
            'Dummy', host_ip='https://www.accelize.com')
        assert accelerator._configuration_url == 'dummy_config_url_2'

    # Restore OpenApi client API
    finally:
        rest_api.ConfigurationApi = rest_api_configuration_api


def test_restclient_stop():
    """Tests RESTClient.stop"""
    from apyfal.client.rest import RESTClient
    from apyfal.exceptions import ClientRuntimeException
    import apyfal.client.rest._openapi as rest_api

    # Mock OpenApi REST API StopApi
    is_alive = True
    stop_list = {'app': {'status': 0, 'msg': ''}}
    stop_list_raise = None

    class StopApi:
        """Fake rest_api.StopApi"""
        is_running = True

        def __init__(self, api_client):
            """Store API client"""
            self.api_client = api_client

        @classmethod
        def stop_list(cls):
            """Simulates accelerator stop and returns fake response"""
            # Stop AcceleratorClient
            cls.is_running = False

            # Fake error
            if stop_list_raise:
                raise rest_api.rest.ApiException

            # Return result
            return stop_list

    # Mock some accelerators parts
    class DummyAccelerator(RESTClient):
        """Dummy AcceleratorClient"""

        def _is_alive(self):
            """Raise on demand"""
            if not is_alive:
                raise ClientRuntimeException()

    # Monkey patch OpenApi client with mocked API
    rest_api_stop_api = rest_api.StopApi
    rest_api.StopApi = StopApi

    # Tests
    try:
        # AcceleratorClient to stop
        accelerator = DummyAccelerator('Dummy')
        assert accelerator.stop(info_dict=True) == stop_list
        assert not StopApi.is_running

        # Ignore OpenApi exceptions
        stop_list_raise = True
        assert DummyAccelerator('Dummy').stop(
            info_dict=True) is None
        assert not StopApi.is_running
        stop_list_raise = False

        # Auto-stops with context manager
        StopApi.is_running = True
        with DummyAccelerator('Dummy') as accelerator:
            # Checks __enter__ returned object
            assert isinstance(accelerator, RESTClient)
        assert not StopApi.is_running

        # Auto-stops on garbage collection
        StopApi.is_running = True
        DummyAccelerator('Dummy')
        gc.collect()
        assert not StopApi.is_running

        # No accelerator to stop
        is_alive = False
        assert DummyAccelerator('Dummy').stop(
            info_dict=True) is None

    # Restore OpenApi client API
    finally:
        rest_api.StopApi = rest_api_stop_api


def test_restclient_process_curl():
    """Tests RESTClient._process_curl with PycURL"""
    # Skip if PycURL not available
    try:
        import pycurl
    except ImportError:
        pytest.skip('Pycurl module required')
        return

    # Check PycURL is enabled in accelerator API
    import apyfal.client.rest
    assert apyfal.client.rest._USE_PYCURL

    # Start testing
    from apyfal.client.rest import RESTClient
    from apyfal.exceptions import ClientRuntimeException

    # Mock some accelerators parts
    class DummyAccelerator(RESTClient):
        """Dummy AcceleratorClient"""

        def __del__(self):
            """Does nothing"""

    # Mock PycURL
    pycurl_curl = pycurl.Curl
    perform_raises = False
    api_response = ''

    class Curl:
        """Fake cURL that don"t communicate"""
        mock_write = None

        def __init__(self):
            self.curl = pycurl_curl()

        def perform(self):
            """Don't communicated but write in buffer"""
            # Simulate exception
            if perform_raises:
                raise pycurl.error

            # Write api_response
            self.mock_write.write(api_response.encode())

        def setopt(self, *args):
            """set cURL options and intercept WRITEDATA"""
            if args[0] == pycurl.WRITEDATA:
                self.mock_write = args[1]
            self.curl.setopt(*args)

        def close(self):
            """Close curl"""
            self.curl.close()

    pycurl.Curl = Curl

    # Tests
    try:
        # Mock some variables
        dummy_parameters = 'dummy_accelerator_parameters'
        dummy_datafile = 'dummy_datafile'

        accelerator = DummyAccelerator('Dummy')
        accelerator._configuration_url = 'dummy_configuration'

        # Test if work as excepted
        expected_response = {'id': 'dummy_id', 'processed': 'dummy_processed'}
        api_response = json.dumps(expected_response)
        response_id, processed = accelerator._process_curl(
            dummy_parameters, dummy_datafile)
        assert response_id == expected_response['id']
        assert processed == expected_response['processed']

        # Test: Invalid response
        api_response = '{id: corrupted_data'
        with pytest.raises(ClientRuntimeException):
            accelerator._process_curl(
                dummy_parameters, dummy_datafile)

        # Test: No id in response
        api_response = '{}'
        with pytest.raises(ClientRuntimeException):
            accelerator._process_curl(
                dummy_parameters, dummy_datafile)

        # Test: Curl.perform raise Exception
        perform_raises = True
        with pytest.raises(ClientRuntimeException):
            accelerator._process_curl(
                dummy_parameters, dummy_datafile)

    # Restore PycURL
    finally:
        pycurl.Curl = pycurl_curl


def test_restclient_process_openapi():
    """Tests RESTClient._process_openapi with OpenApi"""
    # Clean imported modules
    # to force to reimport without PycURL if present
    pycurl_module = sys.modules.get('pycurl')
    if pycurl_module is not None:
        sys.modules['pycurl'] = None
        for module in list(sys.modules):
            if module.startswith('apyfal.client.rest'):
                del sys.modules[module]
        gc.collect()

    # Check PycURL is disabled in accelerator API
    import apyfal.client.rest
    assert not apyfal.client.rest._USE_PYCURL

    # Starts testing with PycURL disabled
    try:
        from apyfal.client.rest import RESTClient
        import apyfal.client.rest._openapi as rest_api

        # Mock some variables
        dummy_id = 'dummy_id'
        dummy_processed = 'dummy_processed'
        dummy_parameters = 'dummy_accelerator_parameters'
        dummy_datafile = 'dummy_datafile'
        dummy_configuration = 'dummy_configuration'

        # Mocks OpenApi REST API ProcessApi
        class ProcessApi:
            """Fake rest_api.ProcessApi"""

            def __init__(self, api_client):
                """Store API client"""
                self.api_client = api_client

            @staticmethod
            def process_create(configuration, parameters, datafile):
                """Checks input arguments and returns fake response"""
                assert parameters == dummy_parameters
                assert datafile == dummy_datafile
                assert configuration == dummy_configuration

                # Return fake response
                Response = collections.namedtuple('Response',
                                                  ['processed', 'id'])
                return Response(id=dummy_id, processed=dummy_processed)

        # Mock some accelerators parts
        class DummyAccelerator(RESTClient):
            """Dummy AcceleratorClient"""

            def __del__(self):
                """Does nothing"""

        # Monkey patch OpenApi client with mocked API
        rest_api_process_api = rest_api.ProcessApi
        rest_api.ProcessApi = ProcessApi

        # Tests
        try:
            # Test if work as excepted
            accelerator = DummyAccelerator('Dummy')
            accelerator._configuration_url = dummy_configuration

            response_id, processed = accelerator._process_openapi(
                dummy_parameters, dummy_datafile)
            assert response_id == dummy_id
            assert processed == dummy_processed

        # Restore OpenApi API
        finally:
            rest_api.ProcessApi = rest_api_process_api

    # Restores PycURL
    finally:
        if pycurl_module is not None:
            sys.modules['pycurl'] = pycurl_module
            for module in list(sys.modules):
                if module.startswith('apyfal.client.rest'):
                    del sys.modules[module]
            gc.collect()


def test_restclient_process(tmpdir):
    """Tests RESTClient._process"""
    import apyfal.exceptions as exc
    import apyfal.client.rest._openapi as rest_api
    from apyfal.client.rest import RESTClient

    # Creates temporary output dir and file in
    tmp_dir = tmpdir.dirpath()
    file_in = tmp_dir.join('file_in.txt')
    dir_out = tmp_dir.join('subdir')
    file_out = dir_out.join('file_out.txt')

    # Mocks some variables
    processed = False
    in_error = True
    specific = {'result': '1'}
    parameters_result = {'app': {
        'status': 0,
        'msg': 'dummy_parameters_result',
        'specific': specific}}
    datafile_result = {'app': {
        'status': 0, 'msg': 'dummy_datafile_result'}}
    out_content = b'file out content'

    # Mocks OpenApi REST API ProcessApi
    class ProcessApi:
        """Fake rest_api.ProcessApi"""

        def __init__(self, api_client):
            """Store API client"""
            self.api_client = api_client

        @staticmethod
        def process_read(id_value):
            """Checks input arguments and returns fake response"""
            Response = collections.namedtuple(
                'Response', ['processed', 'inerror',
                             'parametersresult', 'datafileresult'])

            # Check parameters
            assert id_value == 'dummy_id'

            # Returns response
            return Response(
                processed=True, inerror=in_error,
                parametersresult=json.dumps(parameters_result),
                datafileresult=json.dumps(datafile_result))

        @staticmethod
        def process_delete(id_value):
            """Checks input arguments"""
            # Check parameters
            assert id_value == 'dummy_id'

    # Mock some accelerators parts
    class DummyAccelerator(RESTClient):
        """Dummy AcceleratorClient"""

        def _process_openapi(self, accelerator_parameters, datafile):
            """Mocks process function (tested separately)

            Checks input arguments and returns fake response"""
            # Checks input parameters
            assert json.loads(
                accelerator_parameters) == self._process_parameters
            assert datafile == file_in

            # Returns fake result
            return 'dummy_id', processed

        _process_curl = _process_openapi

        def __del__(self):
            """Does nothing"""

    # Mocks requests in utilities
    class DummySession(requests.Session):
        """Fake requests.Session"""

        @staticmethod
        def get(datafile_result_arg, **_):
            """Checks input arguments and returns fake response"""
            Response = collections.namedtuple('Response', ['raw'])

            # Checks input parameters
            assert json.loads(datafile_result_arg) == datafile_result

            # Returns fake response
            return Response(raw=io.BytesIO(out_content))

    # Monkey patch OpenApi client with mocked API
    openapi_client_process_api = rest_api.ProcessApi
    rest_api.ProcessApi = ProcessApi

    # Monkey patch requests in utilities
    requests_session = requests.Session
    requests.Session = DummySession

    # Tests
    try:
        # Test accelerator not configured
        accelerator = DummyAccelerator('Dummy')
        with pytest.raises(exc.ClientConfigurationException):
            accelerator.process()

        accelerator._configuration_url = 'dummy_configuration'

        # Test input file not exists
        with pytest.raises(exc.ClientConfigurationException):
            accelerator.process(str(file_in), str(file_out))

        # Creates input file
        file_in.write('file in content')
        assert file_in.check(file=True)

        # Test result "inerror" and output-dir creation
        assert not dir_out.check(dir=True)

        with pytest.raises(exc.ClientRuntimeException):
            accelerator.process(str(file_in), str(file_out))

        assert dir_out.check(dir=True)

        # Sets to not in error
        in_error = False

        # Check if working as excepted
        assert accelerator.process(
            str(file_in), str(file_out), info_dict=True) == (
                   specific, parameters_result)
        assert file_out.read_binary() == out_content

        # Checks without info_dict
        assert accelerator.process(str(file_in), str(file_out)) == specific

        # Checks without result
        del parameters_result['app']['specific']
        assert accelerator.process(str(file_in), str(file_out)) == dict()

    # Restore requests and OpenApi API
    finally:
        requests.Session = requests_session
        rest_api.ProcessApi = openapi_client_process_api
