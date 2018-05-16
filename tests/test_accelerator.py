# coding=utf-8
"""acceleratorAPI.accelerator tests"""
import collections
import json

import pytest


def test_accelerator_check_accelize_credential():
    """Tests Accelerator._check_accelize_credential"""
    from acceleratorAPI.configuration import Configuration
    from acceleratorAPI.accelerator import Accelerator
    from acceleratorAPI.exceptions import AcceleratorAuthenticationException

    config = Configuration()

    # Skip test if Accelize credentials not available
    if not config.has_accelize_credential():
        pytest.skip('Accelize Credentials required')

    # Assuming Accelize credentials in configuration file are valid, should pass
    Accelerator('dummy', config=config)

    # Bad client_id
    with pytest.raises(AcceleratorAuthenticationException):
        Accelerator('dummy', config=config, client_id='bad_client_id')

    # Bad secret_id
    with pytest.raises(AcceleratorAuthenticationException):
        Accelerator('dummy', config=config, client_id='bad_secret_id')


def test_is_alive():
    """Tests Accelerator._raise_for_status"""
    from acceleratorAPI.accelerator import Accelerator
    from acceleratorAPI.exceptions import AcceleratorRuntimeException

    accelerator = Accelerator('dummy')

    # No instance
    with pytest.raises(AcceleratorRuntimeException):
        accelerator.is_alive()

    # URL not exist
    accelerator.url = 'http://127.0.0.1/url_that_not_exists'
    with pytest.raises(AcceleratorRuntimeException):
        accelerator.is_alive()

    # URL exists
    accelerator.url = 'https://www.accelize.com/'
    accelerator.is_alive()


def test__raise_for_status():
    """Tests Accelerator._raise_for_status"""
    from acceleratorAPI.accelerator import Accelerator
    from acceleratorAPI.exceptions import AcceleratorRuntimeException

    # Result without error
    Accelerator._raise_for_status({'app': {'status': 0, 'msg': ''}})

    # Empty result
    with pytest.raises(AcceleratorRuntimeException):
        Accelerator._raise_for_status({})

    # Result with error
    with pytest.raises(AcceleratorRuntimeException):
        Accelerator._raise_for_status({'app': {'status': 1, 'msg': 'error'}})


def test_get_accelerator_requirements():
    """Tests Accelerator.get_accelerator_requirements"""
    from acceleratorAPI.configuration import Configuration
    from acceleratorAPI.accelerator import Accelerator
    from acceleratorAPI.exceptions import AcceleratorConfigurationException

    config = Configuration()

    # Skip test if Accelize credentials not available
    if not config.has_accelize_credential():
        pytest.skip('Accelize Credentials required')

    # Invalid Accelerator name
    accelerator = Accelerator('accelerator_not_exists', config=config)
    with pytest.raises(AcceleratorConfigurationException):
        accelerator.get_accelerator_requirements('OVH')

    # Provider not exists
    accelerator = Accelerator('axonerve_hyperfire', config=config)
    with pytest.raises(AcceleratorConfigurationException):
        accelerator.get_accelerator_requirements('no_exist_CSP')

    # Everything OK
    name = 'axonerve_hyperfire'
    accelerator = Accelerator(name, config=config)
    response = accelerator.get_accelerator_requirements('OVH')

    assert response['accelerator'] == name


def test_start_accelerator():
    """Tests Accelerator.start_accelerator"""
    from acceleratorAPI.accelerator import Accelerator

    # Mock Swagger REST API ConfigurationApi
    excepted_parameters = None
    excepted_datafile = None
    configuration_read_in_error = 0

    base_parametersresult = {
                'app': {
                    'status': 0,
                    'msg': 'dummy_msg'}}

    class ConfigurationApi:
        """Fake swagger_client.ConfigurationApi"""

        def configuration_create(self, parameters, datafile):
            """Check input arguments and return fake response"""

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

        def configuration_read(self, id_value):
            """Check input arguments and return fake response"""
            Response = collections.namedtuple('Response', ['inerror', 'id', 'url'])

            # TODO: Check input

            return Response(url='dummy_url', id=id_value, inerror=configuration_read_in_error)

    class DummyAccelerator(Accelerator):
        def __init__(self, *args, **kwargs):
            """Do not initialize"""
            self._client_id = 'dummmy_client_id'
            self._secret_id = 'dummmy_secret_id'
            self._configuration_parameters = self.DEFAULT_CONFIGURATION_PARAMETERS

        def _rest_api_configuration(self):
            """Return Mocked REST API"""
            return ConfigurationApi()

        @property
        def url(self):
            """Fake URL"""
            return 'dummmy_accelerator_url'

    accelerator = DummyAccelerator('dummy')

    base_parameters = {
        "env": {
            "client_id": accelerator.client_id,
            "client_secret": accelerator.secret_id}}

    base_response = {'url_config': 'dummy_url',
                     'url_instance': accelerator.url}

    # Check normal use
    # TODO: WIP
    accelerator_parameters = {'dummy_param': None}
    excepted_parameters = base_parameters.copy()
    excepted_parameters.update(accelerator_parameters)
    excepted_datafile = 'dummy_datafile'
    excepted_response = base_response.copy()

    assert excepted_response == accelerator.start_accelerator(
        datafile=excepted_datafile,
        accelerator_parameters=accelerator_parameters)

    # Check default values
    excepted_datafile = ''

    excepted_parameters = base_parameters.copy()
    excepted_parameters.update(accelerator.DEFAULT_CONFIGURATION_PARAMETERS)

    excepted_response = base_response.copy()
    excepted_response.update(base_parametersresult)

    assert excepted_response == accelerator.start_accelerator()
