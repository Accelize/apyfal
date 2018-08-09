# coding=utf-8
"""apyfal.client tests"""
import copy
import json
from os.path import isdir

import pytest


def test_acceleratorclient_new_init():
    """Tests AcceleratorClient.__new__ and __init__"""
    from apyfal.client import AcceleratorClient
    from apyfal.client.rest import RESTClient

    # Test: Subclass selection
    client = AcceleratorClient('dummy_accelerator', client_type='REST')
    assert isinstance(client, RESTClient)

    # Test: repr
    assert repr(client) == str(client)


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
        AcceleratorClient._raise_for_status(
            {'app': {'status': 1, 'msg': 'error'}})


def test_acceleratorclient_get_parameters(tmpdir):
    """Tests AcceleratorClient._get_parameters"""
    from apyfal.client import AcceleratorClient
    from apyfal._utilities import recursive_update

    # Mocks some variables
    default_parameters = {'app': {'specific': {}, "key0": 0, "key1": 1}}

    # Mocks Client
    class DummyClient(AcceleratorClient):
        """Dummy Client"""

        def _start(self, *_):
            """Do nothing"""

        def _process(self, *_):
            """Do nothing"""

        def _stop(self, *_):
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
    recursive_update(excepted_parameters, dummy_parameters)

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
    recursive_update(excepted_parameters, dummy_parameters)
    excepted_parameters['app']['specific'].update({'key0': 0, 'key1': 0})
    assert client.function(
        parameters=dummy_parameters, key0=0, key1=0) == excepted_parameters

    # Test: Missing specific section in source
    excepted_parameters = copy.deepcopy(default_parameters)
    del default_parameters['app']['specific']
    excepted_parameters['app']['specific'] = {'key0': 0, 'key1': 1}
    assert client.function(key0=0, key1=1) == excepted_parameters


def test_data_file(tmpdir):
    """Tests AcceleratorClient._data_file"""
    from apyfal.client import AcceleratorClient
    from apyfal.exceptions import (
        ClientConfigurationException, ClientSecurityException)

    # Initialize some values
    parameters = {'app': {'specific': {}}}
    content = 'dummy_content'.encode()
    parameter_name = 'dummy_name'
    file_in = tmpdir.join('in')
    file_in.write(content)
    file_in_path = str(file_in)
    file_out = tmpdir.join('sub_dir').join('out')
    file_out_path = str(file_out)
    authorized_dir = tmpdir.join('authorized')

    # Mocks Client
    class DummyClient(AcceleratorClient):
        """Dummy Client"""

        REMOTE = False
        PARAMETER_IO_FORMAT = {parameter_name: 'file'}

        def __init__(self, *_, **__):
            """Do nothing"""
            self._cache = {'tmp_dir': str(tmpdir)}
            self._authorized_host_dirs = [str(authorized_dir)]

        def _start(self, *_):
            """Do nothing"""

        def _process(self, *_):
            """Do nothing"""

        def _stop(self, *_):
            """Do nothing"""

    client = DummyClient()

    # Test: None argument
    with client._data_file(
            None, parameters, parameter_name, 'rb') as path:
        assert path is None

    # Test: Input file
    with client._data_file(
            file_in_path, parameters, parameter_name, 'rb') as path:
        assert path == file_in_path
        with open(path, 'rb') as file:
            assert file.read() == content

    # Test: Input file not exists
    with pytest.raises(ClientConfigurationException):
        with client._data_file(
                'path_not_exists', parameters, parameter_name, 'rb'):
            pass

    # Test: Output file
    with client._data_file(
            file_out_path, parameters, parameter_name, 'wb') as path:
        assert path == file_out_path
        with open(path, 'wb') as file:
            file.write(content)
        assert file_out.read_binary() == content
    file_out.remove()

    # Test: Input file as stream
    client.PARAMETER_IO_FORMAT[parameter_name] = 'stream'
    with client._data_file(
            file_in_path, parameters, parameter_name, 'rb') as file:
        assert file.read() == content
    client.PARAMETER_IO_FORMAT[parameter_name] = 'file'

    # Test: Input stream
    with open(file_in_path, 'rb') as file:
        with client._data_file(file, parameters, parameter_name, 'rb') as path:
            with open(path, 'rb') as tmp_file:
                assert tmp_file.read() == content

    # Test: Output stream
    with open(file_out_path, 'wb') as file:
        with client._data_file(
                file, parameters, parameter_name, 'wb') as path:
            with open(path, 'wb') as tmp_file:
                tmp_file.write(content)
    assert file_out.read_binary() == content

    # host://: Unauthorized dir
    with pytest.raises(ClientSecurityException):
        with client._data_file(
                'host://%s' % file_in_path, parameters,
                parameter_name, 'rb'):
            pass

    # host://: Authorized dir
    authorized_file_in = authorized_dir.join('in')
    authorized_file_in.ensure()
    authorized_file_in_path = str(authorized_file_in)
    with client._data_file(
            'host://%s' % authorized_file_in_path,
            parameters, parameter_name, 'rb') as path:
        assert path == authorized_file_in_path

    # Remote mode: No change for file
    client.REMOTE = True
    with client._data_file(
            file_in_path, parameters, parameter_name, 'rb') as path:
        assert path == file_in_path
    assert not parameters['app']['specific']

    # Remote mode: No change for stream
    with open(file_in_path, 'rb') as file:
        with client._data_file(
                file, parameters, parameter_name, 'rb') as path:
            assert path is not None
    assert not parameters['app']['specific']

    # Remote mode: Others in parameters
    url = 'host://%s' % authorized_file_in_path
    with client._data_file(
            url, parameters, parameter_name, 'rb') as path:
        assert path is None
    assert parameters['app']['specific'][parameter_name] == url

    # Reload from parameters
    parameters['app']['specific'][parameter_name] = file_in_path
    assert parameters['app']['specific'][parameter_name] == file_in_path
    with client._data_file(
            None, parameters, parameter_name, 'rb') as path:
        assert path == file_in_path
    assert not parameters['app']['specific']

    # Try reload from parameters, but not found
    with client._data_file(
            None, parameters, parameter_name, 'rb') as path:
        assert path is None


def test_tmp_dir():
    """Tests AcceleratorClient._tmp_dir"""
    from apyfal.client import AcceleratorClient

    # Mocks Client
    class DummyClient(AcceleratorClient):
        """Dummy Client"""

        def _start(self, *_):
            """Do nothing"""

        def _process(self, *_):
            """Do nothing"""

        def _stop(self, *_):
            """Do nothing"""

    client = DummyClient('dummy')
    assert not client._cache

    # First call: new temporary directory
    tmp_dir = client._tmp_dir
    assert tmp_dir == client._cache.get('tmp_dir')
    assert isdir(tmp_dir)

    # Next call: use previous directory
    assert tmp_dir == client._tmp_dir

    # Stop: Clear directory and cache
    client.stop()
    assert not client._cache
    assert not isdir(tmp_dir)
