# coding=utf-8
"""apyfal.client tests"""
import copy
import json

import pytest


def test_acceleratorclient_new_init():
    """Tests AcceleratorClient.__new__ and __init__"""
    from apyfal.client import AcceleratorClient
    from apyfal.exceptions import ClientConfigurationException

    accelerator = 'dummy_accelerator'
    # Mock Client subclass

    class DummyClient(AcceleratorClient):
        def start(self, *_, **__):
            """Do nothing"""

        def process(self, *_, **__):
            """Do nothing"""

        def stop(self, *_, **__):
            """Do nothing"""

    # Test: host_ip
    client = DummyClient(accelerator)
    assert client.url is None

    host_ip = 'https://www.accelize.com/'
    client = DummyClient(accelerator, host_ip=host_ip)
    assert client.url == host_ip

    with pytest.raises(ClientConfigurationException):
        client.url = None

    with pytest.raises(ValueError):
        DummyClient(accelerator, host_ip='invalid_url')

    # Test: Subclass selection
    AcceleratorClient(accelerator)


def test_acceleratorclient_raise_for_status():
    """Tests AcceleratorClient._raise_for_status"""
    from apyfal.client import AcceleratorClient
    from apyfal.exceptions import ClientRuntimeException

    # Test: Result without error
    AcceleratorClient._raise_for_status({'app': {'status': 0, 'msg': ''}})

    # Test: Empty result
    with pytest.raises(ClientRuntimeException):
        AcceleratorClient._raise_for_status({})

    # Test: Result with error
    with pytest.raises(ClientRuntimeException):
        AcceleratorClient._raise_for_status({'app': {'status': 1, 'msg': 'error'}})


def test_acceleratorclient_get_parameters(tmpdir):
    """Tests AcceleratorClient._get_parameters"""
    from apyfal.client import AcceleratorClient

    # Mocks some variables
    default_parameters = {'app': {'specific': {}, "key0": 0, "key1": 1}}

    # Mocks Client
    class DummyClient(AcceleratorClient):
        """Dummy Client"""

        def start(self, *_, **__):
            """Do nothing"""

        def process(self, *_, **__):
            """Do nothing"""

        def stop(self, *_, **__):
            """Do nothing"""

        def function(self, **parameters):
            """Passe parameters to _get_parameters and return result"""
            return self._get_parameters(parameters, default_parameters)

    client = DummyClient('Dummy')

    # Test: Pass specific parameters as keyword arguments
    excepted_parameters = copy.deepcopy(default_parameters)
    excepted_parameters['app']['specific'] = {'key0': 0, 'key1': 1}
    assert client.function(key0=0, key1=1) == excepted_parameters

    # Test: loads parameters dict
    dummy_parameters = {'app': {'specific': {'key1': 1}, "key0": 1}}
    excepted_parameters = copy.deepcopy(default_parameters)
    excepted_parameters.update(dummy_parameters)

    assert client.function(
        parameters=dummy_parameters) == excepted_parameters

    # Test: loads parameters dict as JSON literal
    assert client.function(parameters=json.dumps(
        dummy_parameters)) == excepted_parameters

    # Test: loads parameters dict as JSON file
    json_file = tmpdir.join('parameters.json')
    json_file.write(json.dumps(dummy_parameters))
    assert client.function(parameters=str(json_file)) == excepted_parameters

    # Test: Simultaneous parameters dict + keyword arguments
    excepted_parameters = copy.deepcopy(default_parameters)
    excepted_parameters.update(dummy_parameters)
    excepted_parameters['app']['specific'].update({'key0': 0, 'key1': 0})
    assert client.function(
        parameters=dummy_parameters, key0=0, key1=0) == excepted_parameters

    # Test: Missing specific section in source
    excepted_parameters = copy.deepcopy(default_parameters)
    del default_parameters['app']['specific']
    excepted_parameters['app']['specific'] = {'key0': 0, 'key1': 1}
    assert client.function(key0=0, key1=1) == excepted_parameters
