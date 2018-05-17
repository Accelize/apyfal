# coding=utf-8
"""acceleratorAPI.accelerator tests"""
import collections
import gc
import json
import sys
import tempfile

import pytest


def test_accelerator_check_accelize_credential():
    """Tests AcceleratorClient._check_accelize_credential

    Test parts that needs credentials"""
    from acceleratorAPI.configuration import Configuration
    from acceleratorAPI.accelerator import AcceleratorClient
    from acceleratorAPI.exceptions import AcceleratorAuthenticationException

    config = Configuration()

    # Skip test if Accelize credentials not available
    if not config.has_accelize_credential():
        pytest.skip('Accelize Credentials required')

    # Assuming Accelize credentials in configuration file are valid, should pass
    # Called Through AcceleratorClient.__init__
    AcceleratorClient('dummy', config=config)

    # Keep same client_id but use bad secret_id
    with pytest.raises(AcceleratorAuthenticationException):
        AcceleratorClient('dummy', config=config, secret_id='bad_secret_id')


def test_accelerator_check_accelize_credential_no_cred():
    """Tests AcceleratorClient._check_accelize_credential

    Test parts that don't needs credentials"""
    from acceleratorAPI.configuration import Configuration
    from acceleratorAPI.accelerator import AcceleratorClient
    import acceleratorAPI.exceptions as exc

    config = Configuration()
    config.remove_section('accelize')

    # No credential provided
    with pytest.raises(exc.AcceleratorConfigurationException):
        AcceleratorClient('dummy', config=config)

    # Bad client_id
    with pytest.raises(exc.AcceleratorAuthenticationException):
        AcceleratorClient('dummy', client_id='bad_client_id',
                          secret_id='bad_secret_id', config=config)


def test_accelerator_is_alive():
    """Tests AcceleratorClient._raise_for_status"""
    from acceleratorAPI.accelerator import AcceleratorClient
    from acceleratorAPI.exceptions import AcceleratorRuntimeException

    class DummyAccelerator(AcceleratorClient):
        """Dummy AcceleratorClient"""

        def __init__(self, url=None):
            """Do not initialize"""
            self._url = url

        def __del__(self):
            """Do nothing"""

    # No instance
    accelerator = DummyAccelerator()
    with pytest.raises(AcceleratorRuntimeException):
        accelerator.is_alive()

    # URL exists
    accelerator = DummyAccelerator(url='https://www.accelize.com')
    accelerator.is_alive()

    # URL not exist
    accelerator = DummyAccelerator(url='https://www.url_that_not_exists.accelize.com')
    with pytest.raises(AcceleratorRuntimeException):
        accelerator.is_alive()


def test_accelerator_raise_for_status():
    """Tests AcceleratorClient._raise_for_status"""
    from acceleratorAPI.accelerator import AcceleratorClient
    from acceleratorAPI.exceptions import AcceleratorRuntimeException

    # Result without error
    AcceleratorClient._raise_for_status({'app': {'status': 0, 'msg': ''}})

    # Empty result
    with pytest.raises(AcceleratorRuntimeException):
        AcceleratorClient._raise_for_status({})

    # Result with error
    with pytest.raises(AcceleratorRuntimeException):
        AcceleratorClient._raise_for_status({'app': {'status': 1, 'msg': 'error'}})


def test_accelerator_get_requirements():
    """Tests AcceleratorClient.get_requirements"""
    from acceleratorAPI.configuration import Configuration
    from acceleratorAPI.accelerator import AcceleratorClient
    from acceleratorAPI.exceptions import AcceleratorConfigurationException

    config = Configuration()

    # Skip test if Accelize credentials not available
    if not config.has_accelize_credential():
        pytest.skip('Accelize Credentials required')

    # Invalid AcceleratorClient name
    accelerator = AcceleratorClient('accelerator_not_exists', config=config)
    with pytest.raises(AcceleratorConfigurationException):
        accelerator.get_requirements('OVH')

    # Provider not exists
    accelerator = AcceleratorClient('axonerve_hyperfire', config=config)
    with pytest.raises(AcceleratorConfigurationException):
        accelerator.get_requirements('no_exist_CSP')

    # Everything OK
    name = 'axonerve_hyperfire'
    accelerator = AcceleratorClient(name, config=config)
    response = accelerator.get_requirements('OVH')

    assert response['accelerator'] == name


def test_accelerator_start():
    """Tests AcceleratorClient.start"""
    from acceleratorAPI.accelerator import AcceleratorClient
    from acceleratorAPI.exceptions import AcceleratorRuntimeException

    # Mock Swagger REST API ConfigurationApi
    excepted_parameters = None
    excepted_datafile = None
    configuration_read_in_error = 0

    base_parametersresult = {
        'app': {'status': 0, 'msg': 'dummy_msg'}}

    class ConfigurationApi:
        """Fake swagger_client.ConfigurationApi"""

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
                parametersresult=json.dumps(base_parametersresult))

        @staticmethod
        def configuration_read(id_value):
            """Checks input arguments and returns fake response"""
            Response = collections.namedtuple('Response', ['inerror', 'id', 'url'])

            # Check parameters
            assert id_value == 'dummy_id'

            # Return response
            return Response(url='dummy_url', id=id_value, inerror=configuration_read_in_error)

    class DummyAccelerator(AcceleratorClient):
        """Dummy AcceleratorClient"""

        def __init__(self):
            """Do not initialize"""
            self._client_id = 'dummmy_client_id'
            self._secret_id = 'dummmy_secret_id'
            self._configuration_parameters = self.DEFAULT_CONFIGURATION_PARAMETERS

        def __del__(self):
            """Do nothing"""

        def _rest_api_configuration(self):
            """Returns Mocked REST API"""
            return ConfigurationApi()

        @property
        def url(self):
            """Fake URL"""
            return 'dummy_accelerator_url'

    accelerator = DummyAccelerator()

    base_parameters = {
        "env": {
            "client_id": accelerator.client_id,
            "client_secret": accelerator.secret_id}}

    base_response = {'url_config': 'dummy_url',
                     'url_instance': accelerator.url}

    # Check with arguments
    accelerator_parameters = {'dummy_param': None}
    excepted_parameters = base_parameters.copy()
    excepted_parameters.update(accelerator_parameters)
    excepted_datafile = 'dummy_datafile'
    excepted_response = base_response.copy()
    excepted_response.update(base_parametersresult)

    assert excepted_response == accelerator.start(
        datafile=excepted_datafile,
        accelerator_parameters=accelerator_parameters)

    # Check default values
    excepted_datafile = ''
    excepted_parameters = base_parameters.copy()
    excepted_parameters.update(accelerator.DEFAULT_CONFIGURATION_PARAMETERS)
    excepted_response = base_response.copy()
    excepted_response.update(base_parametersresult)

    assert excepted_response == accelerator.start()

    # Check error from host
    configuration_read_in_error = 1
    with pytest.raises(AcceleratorRuntimeException):
        assert excepted_response == accelerator.start()


def test_accelerator_use_last_configuration():
    """Tests AcceleratorClient._use_last_configuration"""
    from acceleratorAPI.accelerator import AcceleratorClient

    # Mock Swagger REST API ConfigurationApi
    Config = collections.namedtuple('Config', ['url', 'used'])
    config_list = []

    class ConfigurationApi:
        """Fake swagger_client.ConfigurationApi"""

        @staticmethod
        def configuration_list():
            """Returns fake response"""
            Response = collections.namedtuple('Response', ['results'])
            return Response(results=config_list)

    class DummyAccelerator(AcceleratorClient):
        """Dummy AcceleratorClient"""

        def __del__(self):
            """Do nothing"""

        def _rest_api_configuration(self):
            """Return Mocked REST API"""
            return ConfigurationApi()

        def _check_accelize_credential(self):
            """Don't check credential"""

    # Check method, Called through AcceleratorClient.url, through AcceleratorClient.__init__

    # No previous configuration
    accelerator = DummyAccelerator('Dummy', url='https://www.accelize.com')
    assert accelerator.configuration_url is None

    # Unused previous configuration
    config_list.append(Config(url='dummy_config_url', used=0))
    accelerator = DummyAccelerator('Dummy', url='https://www.accelize.com')
    assert accelerator.configuration_url is None

    # Used previous configuration
    config_list.insert(0, Config(url='dummy_config_url_2', used=1))
    accelerator = DummyAccelerator('Dummy', url='https://www.accelize.com')
    assert accelerator.configuration_url == 'dummy_config_url_2'


def test_accelerator_stop():
    """Tests AcceleratorClient.stop"""
    from acceleratorAPI.accelerator import AcceleratorClient
    from acceleratorAPI.exceptions import AcceleratorRuntimeException

    # Mock Swagger REST API StopApi
    is_alive = True
    stop_list = {'app': {'status': 0, 'msg': ''}}

    class StopApi:
        """Fake swagger_client.StopApi"""
        is_running = True

        def stop_list(self):
            """Simulates accelerator stop and returns fake response"""
            # Stop AcceleratorClient
            self.is_running = False

            # Return result
            return stop_list

    stop_api = StopApi()

    class DummyAccelerator(AcceleratorClient):
        """Dummy AcceleratorClient"""

        def __init__(self):
            """Do not initialize"""
            self._name = 'dummy'

        @staticmethod
        def is_alive():
            """Raise on demand"""
            if not is_alive:
                raise AcceleratorRuntimeException()

        @staticmethod
        def _rest_api_stop():
            """Return Mocked REST API"""
            return stop_api

    # AcceleratorClient to stop
    assert DummyAccelerator().stop() == stop_list
    assert not stop_api.is_running

    # Auto-stops with context manager
    stop_api.is_running = True
    with DummyAccelerator() as accelerator:
        # Checks __enter__ returned object
        assert isinstance(accelerator, AcceleratorClient)
    assert not stop_api.is_running

    # Auto-stops on garbage collection
    stop_api.is_running = True
    DummyAccelerator()
    gc.collect()
    assert not stop_api.is_running

    # No accelerator to stop
    is_alive = False
    assert DummyAccelerator().stop() is None


def test_accelerator_process_curl():
    """Tests AcceleratorClient._process_curl with PycURL"""
    # Skip if PycURL not available
    try:
        import pycurl
    except ImportError:
        pytest.skip('Pycurl module required')

    # Check PycURL is enabled in accelerator API
    import acceleratorAPI.accelerator
    assert acceleratorAPI.accelerator._USE_PYCURL

    # Start testing
    from acceleratorAPI.accelerator import AcceleratorClient
    # TODO: WIP


def test_accelerator_process_swagger():
    """Tests AcceleratorClient._process_swagger with Swagger"""
    # Clean imported modules
    # to force to reimport without PycURL if present
    pycurl_module = sys.modules.get('pycurl')
    if pycurl_module is not None:
        sys.modules['pycurl'] = None
        try:
            del sys.modules['acceleratorAPI.accelerator']
        except KeyError:
            pass
        gc.collect()

    # Check PycURL is disabled in accelerator API
    import acceleratorAPI.accelerator
    assert not acceleratorAPI.accelerator._USE_PYCURL

    # Starts testing
    try:
        from acceleratorAPI.accelerator import AcceleratorClient
        # TODO: WIP

    # Restores before test state
    finally:
        if pycurl_module is not None:
            sys.modules['pycurl'] = pycurl_module
            try:
                del sys.modules['acceleratorAPI.accelerator']
            except KeyError:
                pass
            gc.collect()


def test_accelerator_process():
    """Tests AcceleratorClient._process"""
    from acceleratorAPI.accelerator import AcceleratorClient

    # Mock Swagger REST API ProcessApi

    class ProcessApi:
        """Fake swagger_client.ProcessApi"""

        @staticmethod
        def process_read(id_value):
            """Checks input arguments and returns fake response"""
            Response = collections.namedtuple(
                'Response',
                ['processed', 'inerror', 'parametersresult', 'datafileresult'])

            # Check parameters
            assert id_value == 'dummy_id'

            return Response()

        @staticmethod
        def process_delete(id_value):
            """Checks input arguments"""
            # Check parameters
            assert id_value == 'dummy_id'

    def process_function(accelerator_parameters, datafile):
        """Mock process function (tested separately)"""

    class DummyAccelerator(AcceleratorClient):
        """Dummy AcceleratorClient"""

        _process_curl = process_function
        _process_swagger = process_function

        def __init__(self):
            """Do not initialize"""
            self._process_parameters = self.DEFAULT_PROCESS_PARAMETERS
            self._configuration_url = None

        def __del__(self):
            """Do nothing"""

        @staticmethod
        def _rest_api_process():
            """Return Mocked REST API"""
            return ProcessApi()

    # TODO: WIP
    tmp_dir = tempfile.mkdtemp()
    try:
        pass

    finally:
        # TODO: clean tmp_dir
        pass
