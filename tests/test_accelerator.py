# coding=utf-8
"""apyfal tests"""
from collections import namedtuple
import gc
import sys
from time import sleep


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
    dummy_url = 'http://accelize.com'
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
    process_duration = 0.0

    # Mocks client
    accelerator_client_class = apyfal.client.AcceleratorClient

    class DummyClient(accelerator_client_class):
        """Dummy apyfal.client.AcceleratorClient"""
        url = None
        running = True

        def __new__(cls, *args, **kwargs):
            return object.__new__(cls)

        def __init__(self, accelerator, host_ip=None, **kwargs):
            """Checks arguments"""
            self.url = host_ip
            accelerator_client_class.__init__(self, accelerator, **kwargs)
            assert accelerator == dummy_accelerator

        def __del__(self):
            """Don nothing"""

        def _start(self, *_):
            """Do Nothing"""

        def _stop(self, *_):
            """Do Nothing"""

        def _process(self, *_):
            """Do Nothing"""

        def start(self, datafile=None, host_env=None, info_dict=True,
                  reset=False, reload=False, **parameters):
            """Checks arguments and returns fake result"""
            assert datafile == dummy_datafile
            assert parameters == {'parameters': dummy_accelerator_parameters}
            return dummy_start_result

        def stop(self, info_dict=True, **_):
            """Returns fake result"""
            DummyClient.running = False

            if raises_on_client_stop:
                # Raises exception
                raise ClientException

            return dummy_stop_result

        def process(self, file_in=None, file_out=None, info_dict=True,
                    **parameters):
            """Checks arguments and returns fake result"""
            assert parameters == {'parameters': dummy_accelerator_parameters}
            assert file_in == dummy_file_in
            assert file_out == dummy_file_out
            sleep(process_duration)
            return dummy_process_result

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

        # Start
        assert accel.start(
            datafile=dummy_datafile, stop_mode=dummy_stop_mode, info_dict=True,
            parameters=dummy_accelerator_parameters) == dummy_start_result
        assert accel.client.url == dummy_url

        # Process
        assert accel.process(
            file_in=dummy_file_in, file_out=dummy_file_out, info_dict=True,
            parameters=dummy_accelerator_parameters) == dummy_process_result

        # Async Process
        process_duration = 0.05
        future = accel.process_submit(
            file_in=dummy_file_in, file_out=dummy_file_out, info_dict=True,
            parameters=dummy_accelerator_parameters
            )
        assert accel.process_running_count == 1
        assert future.result() == dummy_process_result
        sleep(0.05)  # Avoid some Python 2 timing issues
        assert accel.process_running_count == 0

        # Stop
        assert accel.stop(stop_mode=dummy_stop_mode,
                          info_dict=True) == dummy_stop_result
        assert not DummyClient.running
        assert not DummyHost.running

        # Repr
        assert repr(accel) == str(accel)

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


def test_accelerator_get_host():
    """Tests Accelerator._get_host"""
    from apyfal import Accelerator
    import apyfal.configuration as cfg

    # Get an empty configuration
    config = cfg.Configuration()
    try:
        del config._sections['host']
    except KeyError:
        pass

    # Get static method to test
    get_host = Accelerator._get_host

    # Mock accelerator_executable_available
    is_localhost = False

    def accelerator_executable_available():
        """Returns fake result"""
        return is_localhost

    cfg_accelerator_available = cfg.accelerator_executable_available
    cfg.accelerator_executable_available = accelerator_executable_available

    # Tests
    try:
        # Not local, but should be see as local
        is_localhost = False

        host_type = None
        assert get_host(
            config, host_type, prefer_self_hosted=False) == (host_type, True)

        host_type = 'localhost'
        assert get_host(
            config, host_type, prefer_self_hosted=False) == (host_type, True)

        # Is local
        is_localhost = True

        host_type = None
        assert get_host(
            config, host_type, prefer_self_hosted=False) == (host_type, True)
        assert get_host(
            config, host_type, prefer_self_hosted=True) == (host_type, True)

        host_type = 'localhost'
        assert get_host(
            config, host_type, prefer_self_hosted=False) == (host_type, True)
        assert get_host(
            config, host_type, prefer_self_hosted=True) == (host_type, True)

        host_type = 'host_type'
        assert get_host(
            config, host_type, prefer_self_hosted=True) == (host_type, True)

        # Should select remote
        assert get_host(
            config, host_type, prefer_self_hosted=False) == (host_type, False)

        is_localhost = False
        assert get_host(
            config, host_type, prefer_self_hosted=True) == (host_type, False)
        assert get_host(
            config, host_type, prefer_self_hosted=False) == (host_type, False)

        # Get from configuration or default value
        is_localhost = True
        config['host']['host_type'] = host_type

        assert get_host(
            config, host_type=None, prefer_self_hosted=None) == (
            host_type, True)

        config['host']['prefer_self_hosted'] = False
        assert get_host(
            config, host_type=None, prefer_self_hosted=None) == (
            host_type, False)

    # Restore mocked function
    finally:
        cfg.accelerator_executable_available = cfg_accelerator_available
