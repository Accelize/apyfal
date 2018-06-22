# coding=utf-8
"""apyfal tests"""
from collections import namedtuple
import gc
import sys

import pytest


def tests_version_check():
    """Test version check presence and format"""
    # Ensure Apyfal not imported
    try:
        del sys.modules['apyfal']
    except KeyError:
        pass
    gc.collect()

    # Mock version info
    sys_version_info = sys.version_info
    version_info = namedtuple(
        'Version_Info',
        ['major', 'minor', 'micro', 'releaselevel', 'serial'])
    sys.version_info = version_info(3, 3, 0, 'final', 0)

    # Test
    try:
        with pytest.raises(ImportError):
            import apyfal

    # Cleaning
    finally:
        sys.version_info = sys_version_info


def test_accelerator():
    """Tests Accelerator"""
    from apyfal import Accelerator
    from apyfal.exceptions import HostException, ClientException
    import apyfal

    # Mocks variables
    raises_on_get_url = False
    raises_on_client_stop = False
    raises_on_host_stop = False
    dummy_url = 'dummy_url'
    dummy_config_url = 'dummy_config_url'
    dummy_start_result = 'dummy_start_result'
    dummy_stop_result = 'dummy_stop_result'
    dummy_process_result = 'dummy_process_result'
    dummy_stop_mode = 'dummy_stop_mode'
    dummy_accelerator = 'dummy_accelerator'
    dummy_host_type = 'dummy_host_type'
    dummy_datafile = 'dummy_datafile'
    dummy_accelerator_parameters = {'dummy_accelerator_parameters': None}
    dummy_file_in = 'dummy_file_in'
    dummy_file_out = 'dummy_file_out'

    # Mocks client
    class DummyClient(apyfal.client.AcceleratorClient):
        """Dummy apyfal.client.AcceleratorClient"""
        url = None
        configuration_url = dummy_config_url
        running = True

        def __init__(self, accelerator, *_, **__):
            """Checks arguments"""
            assert accelerator == dummy_accelerator
            self._name = accelerator

        def __del__(self):
            """Don nothing"""

        def start(self, datafile=None, host_env=None, info_dict=True, **parameters):
            """Checks arguments and returns fake result"""
            assert datafile == dummy_datafile
            assert parameters == {'parameters': dummy_accelerator_parameters}
            return dummy_start_result

        def stop(self, info_dict=True):
            """Returns fake result"""
            DummyClient.running = False

            if raises_on_client_stop:
                # Raises exception
                raise ClientException

            return dummy_stop_result

        def process(self, file_in, file_out, info_dict=True, **parameters):
            """Checks arguments and returns fake result"""
            assert parameters == {'parameters': dummy_accelerator_parameters}
            assert file_in == dummy_file_in
            assert file_out == dummy_file_out
            return dummy_process_result

    accelerator_client_class = apyfal.client.AcceleratorClient
    apyfal.client.AcceleratorClient = DummyClient

    # Mocks Host
    class DummyHost:
        """Dummy apyfal.host.Host"""
        _url = dummy_url
        running = True

        def __init__(self, **kwargs):
            """Checks arguments"""
            assert dummy_host_type in kwargs.values()

        def __del__(self):
            """Don nothing"""

        @property
        def url(self):
            """Raises or returns result normally"""
            if raises_on_get_url:
                # Raises exception
                raise HostException
            return self._url

        @staticmethod
        def start(accelerator, stop_mode):
            """Checks arguments"""
            assert accelerator == dummy_accelerator
            assert stop_mode == dummy_stop_mode

            if raises_on_host_stop:
                # Raises exception
                raise HostException

        @staticmethod
        def stop(stop_mode):
            """Checks arguments"""
            if DummyHost.running:
                assert stop_mode == dummy_stop_mode
            DummyHost.running = False

            if raises_on_host_stop:
                raise HostException

        def get_configuration_env(*_, **__):
            """Do nothing"""

    host_class = apyfal.host.Host
    apyfal.host.Host = DummyHost

    # Tests
    try:
        # Creating New host
        accel = Accelerator(dummy_accelerator, host_type=dummy_host_type)
        assert isinstance(accel.host, DummyHost)
        assert isinstance(accel.client, DummyClient)
        assert DummyClient.running
        assert DummyHost.running
        assert accel.start(
            datafile=dummy_datafile, stop_mode=dummy_stop_mode, info_dict=True,
            parameters=dummy_accelerator_parameters) == dummy_start_result
        assert accel.client.url == dummy_url
        assert accel.process(
            file_in=dummy_file_in, file_out=dummy_file_out, info_dict=True,
            parameters=dummy_accelerator_parameters) == dummy_process_result
        assert accel.stop(stop_mode=dummy_stop_mode, info_dict=True) == dummy_stop_result
        assert not DummyClient.running
        assert not DummyHost.running

        # Using existing IP
        accel = Accelerator(
            dummy_accelerator, host_type=dummy_host_type, host_ip=dummy_url)
        assert accel.client.url == dummy_url

        # Using existing IP that not exists
        raises_on_get_url = True
        accel = Accelerator(
            dummy_accelerator, host_type=dummy_host_type, host_ip=dummy_url)
        assert accel.client.url is None
        raises_on_get_url = False

        # Auto-stops with context manager
        dummy_stop_mode = None
        DummyClient.running = True
        DummyHost.running = True
        with Accelerator(
                dummy_accelerator, host_type=dummy_host_type) as accel:
            assert isinstance(accel, Accelerator)
        assert not DummyClient.running
        assert not DummyHost.running

        # Auto-stops on garbage collection
        DummyClient.running = True
        DummyHost.running = True
        Accelerator(dummy_accelerator, host_type=dummy_host_type)
        gc.collect()
        assert not DummyClient.running
        assert not DummyHost.running

        # Clean stop even if error in client or host
        accel = Accelerator(dummy_accelerator, host_type=dummy_host_type)
        raises_on_client_stop = True
        accel.stop()
        raises_on_client_stop = False

        accel = Accelerator(dummy_accelerator, host_type=dummy_host_type)
        raises_on_host_stop = True
        accel.stop()
        raises_on_host_stop = False

    # Restore classes
    finally:
        apyfal.client.AcceleratorClient = accelerator_client_class
        apyfal.host.Host = host_class
