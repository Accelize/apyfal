# coding=utf-8
"""acceleratorAPI tests"""
import gc


def test_acceleratorclass():
    """Tests AcceleratorClass"""
    from acceleratorAPI import AcceleratorClass
    import acceleratorAPI

    # Mocks variables
    dummy_url = 'dummy_url'
    dummy_config_url = 'dummy_config_url'
    dummy_start_result = 'dummy_start_result'
    dummy_stop_result = 'dummy_stop_result'
    dummy_process_result = 'dummy_process_result'
    dummy_stop_mode = 'dummy_stop_mode'
    dummy_accelerator = 'dummy_accelerator'
    dummy_provider = 'dummy_provider'
    dummy_datafile = 'dummy_datafile'
    dummy_accelerator_parameters = {'dummy_accelerator_parameters': None}
    dummy_file_in = 'dummy_file_in'
    dummy_file_out = 'dummy_file_out'
    dummy_id = 'dummy_id'

    # Mocks client
    class DummyClient(acceleratorAPI.client.AcceleratorClient):
        """Dummy acceleratorAPI.client.AcceleratorClient"""
        url = None
        configuration_url = dummy_config_url
        running = True

        def __init__(self, *args, **_):
            """Checks arguments"""
            assert dummy_accelerator in args

        def __del__(self):
            """Don nothing"""

        def start(self, datafile=None, csp_env=None, info_dict=True, **parameters):
            """Checks arguments and returns fake result"""
            assert datafile == dummy_datafile
            assert parameters == {'parameters': dummy_accelerator_parameters}
            return dummy_start_result

        def stop(self, info_dict=True):
            """Returns fake result"""
            DummyClient.running = False
            return dummy_stop_result

        def process(self, file_in, file_out, info_dict=True, **parameters):
            """Checks arguments and returns fake result"""
            assert parameters == {'parameters': dummy_accelerator_parameters}
            assert file_in == dummy_file_in
            assert file_out == dummy_file_out
            return dummy_process_result

    accelerator_client_class = acceleratorAPI.client.AcceleratorClient
    acceleratorAPI.client.AcceleratorClient = DummyClient

    # Mocks CSP
    class DummyCSP:
        """Dummy acceleratorAPI.csp.CSPGenericClass"""
        url = dummy_url
        running = True

        def __init__(self, **kwargs):
            """Checks arguments"""
            assert dummy_provider in kwargs.values()

        def __del__(self):
            """Don nothing"""

        def instance_status(self):
            """Do nothing"""

        @staticmethod
        def start(accel_client, stop_mode):
            """Checks arguments"""
            assert isinstance(accel_client, DummyClient)
            assert stop_mode == dummy_stop_mode

        @staticmethod
        def stop(stop_mode):
            """Checks arguments"""
            if DummyCSP.running:
                assert stop_mode == dummy_stop_mode
            DummyCSP.running = False

        def get_configuration_env(*_, **__):
            """Do nothing"""

    csp_class = acceleratorAPI.csp.CSPGenericClass
    acceleratorAPI.csp.CSPGenericClass = DummyCSP

    # Tests
    try:
        # Creating New instance
        accelerator = AcceleratorClass(dummy_accelerator, provider=dummy_provider)
        assert isinstance(accelerator.csp, DummyCSP)
        assert isinstance(accelerator.client, DummyClient)
        assert DummyClient.running
        assert DummyCSP.running
        assert accelerator.start(
            datafile=dummy_datafile, stop_mode=dummy_stop_mode, info_dict=True,
            parameters=dummy_accelerator_parameters) == dummy_start_result
        assert accelerator.client.url == dummy_url
        assert accelerator.process(
            file_in=dummy_file_in, file_out=dummy_file_out, info_dict=True,
            parameters=dummy_accelerator_parameters) == dummy_process_result
        assert accelerator.stop(stop_mode=dummy_stop_mode, info_dict=True) == dummy_stop_result
        assert not DummyClient.running
        assert not DummyCSP.running

        # Using existing IP
        accelerator = AcceleratorClass(
            dummy_accelerator, provider=dummy_provider, instance_ip=dummy_url)
        assert accelerator.client.url == dummy_url

        # Using existing instance ID
        accelerator = AcceleratorClass(
            dummy_accelerator, provider=dummy_provider, instance_id=dummy_id)
        assert accelerator.client.url == dummy_url

        # Auto-stops with context manager
        dummy_stop_mode = None
        DummyClient.running = True
        DummyCSP.running = True
        with AcceleratorClass(
                dummy_accelerator, provider=dummy_provider) as accelerator:
            assert isinstance(accelerator, AcceleratorClass)
        assert not DummyClient.running
        assert not DummyCSP.running

        # Auto-stops on garbage collection
        DummyClient.running = True
        DummyCSP.running = True
        AcceleratorClass(dummy_accelerator, provider=dummy_provider)
        gc.collect()
        assert not DummyClient.running
        assert not DummyCSP.running

    # Restore classes
    finally:
        acceleratorAPI.client.AcceleratorClient = accelerator_client_class
        acceleratorAPI.csp.CSPGenericClass = csp_class
