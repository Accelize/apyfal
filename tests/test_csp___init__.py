# coding=utf-8
"""acceleratorAPI.csp tests"""
import gc
import time
import warnings

import pytest


def test_cspgenericclass_new_init():
    """Tests CSPGenericClass.__new__ and CSPGenericClass.__init__"""
    from acceleratorAPI.configuration import Configuration
    from acceleratorAPI.csp import CSPGenericClass
    from acceleratorAPI.csp.ovh import OVHClass
    from acceleratorAPI.exceptions import CSPConfigurationException

    # Mock arguments and configuration
    # Note that provider is not specified here
    config = Configuration()
    config.remove_section('csp')
    kwargs = {'region': 'region', 'project_id': 'project_id', 'client_id': 'client_id',
              'auth_url': 'auth_url', 'interface': 'interface', 'config': config}

    # Test: Existing CSP class and module
    assert isinstance(CSPGenericClass(provider="OVH", **kwargs), OVHClass)

    # Test: Not existing CSP module
    with pytest.raises(CSPConfigurationException):
        CSPGenericClass(provider="no_existing_csp")

    # Test: Existing CSP module, with no valid class
    with pytest.raises(CSPConfigurationException):
        CSPGenericClass(provider="generic_openstack")

    # Test: direct instantiation of subclass without specify provider
    OVHClass(**kwargs)

    # Test: Instantiation of without specify provider
    with pytest.raises(CSPConfigurationException):
        CSPGenericClass(**kwargs)

    # Test: Instantiation with missing mandatory arguments
    with pytest.raises(CSPConfigurationException):
        CSPGenericClass(provider="OVH", config=config)

    kwargs_no_client_id = kwargs.copy()
    del kwargs_no_client_id['client_id']
    with pytest.raises(CSPConfigurationException):
        CSPGenericClass(provider="OVH", **kwargs_no_client_id)

    # Test: Abstract class still working with factory
    class UncompletedCSP(CSPGenericClass):
        """Uncompleted CSP class"""

    with pytest.raises(TypeError):
        UncompletedCSP()


def get_dummy_csp_class():
    """
    Returns a base dummy subclass of CSPGenericClass

    Returns:
        acceleratorAPI.csp.CSPGenericClass subclass
    """
    from acceleratorAPI.csp import CSPGenericClass

    class BaseDummyClass(CSPGenericClass):
        """Base dummy class"""
        NAME = 'Dummy'

        def _get_public_ip(self):
            """Dummy method"""

        def _get_private_ip(self):
            """Dummy method"""

        def _check_credential(self):
            """Dummy method"""

        def _get_status(self):
            """Dummy method"""

        def _get_instance(self):
            """Dummy method"""

        def _init_key_pair(self):
            """Dummy method"""

        def _create_instance(self):
            """Dummy method"""

        def _start_new_instance(self):
            """Dummy method"""

        def _start_existing_instance(self, **kwargs):
            """Dummy method"""

        def _terminate_instance(self):
            """Dummy method"""

        def _pause_instance(self):
            """Dummy method"""

    return BaseDummyClass


def test_cspgenericclass_properties():
    """Tests CSPGenericClass properties"""
    from acceleratorAPI.exceptions import CSPInstanceException

    # Mock variables
    provider = 'dummy_provider'
    public_ip = 'dummy_public_ip'
    private_ip = 'dummy_private_ip'
    url = 'http://127.0.0.1'
    instance_id = 'dummy_instance_id'
    stop_mode = 'keep'
    region = 'dummy_region'

    # Mock CSP class
    class DummyClass(get_dummy_csp_class()):
        """Dummy CSP"""

        def _get_public_ip(self):
            """Returns fake result"""
            return public_ip

        def _get_private_ip(self):
            """Returns fake result"""
            return private_ip

        def _status(self):
            """Do nothing"""

    csp = DummyClass(
        provider=provider, instance_ip=url,
        instance_id=instance_id, stop_mode=stop_mode,
        region=region)
    csp._instance = 'dummy_instance'

    # Test: properties values
    assert csp.provider == provider
    assert csp.public_ip == public_ip
    assert csp.private_ip == private_ip
    assert csp.url == url
    assert csp.instance_id == instance_id
    assert csp.stop_mode == stop_mode

    # Test: Information property
    # 'not_exists' tests case where a value is not defined on class
    # (Example if specific only to some CSP subclasses). But we
    # don't want property crash in this case, only return
    # a dict without not existing values
    csp._INFO_NAMES.add('not_exists')
    info = csp.info
    for name in {
            'provider', 'public_ip',
            'private_ip', 'url',
            'instance_id', 'region', 'stop_mode'}:
        assert info[name] == locals()[name]
    assert 'not_exists' not in info

    # Test: properties if no instance
    csp._instance = None
    with pytest.raises(CSPInstanceException):
        csp.public_ip

    with pytest.raises(CSPInstanceException):
        csp.private_ip

    # Test: Stop mode setter, no change if no value set
    csp.stop_mode = None
    assert csp.stop_mode == stop_mode

    # Test: Stop mode setter, set value as int
    csp.stop_mode = 0
    assert csp.stop_mode == 'term'

    # Test: Stop mode setter, set value as str int
    csp.stop_mode = '0'
    assert csp.stop_mode == 'term'

    # Test: Stop mode setter, set value as str
    csp.stop_mode = 'term'
    assert csp.stop_mode == 'term'

    csp.stop_mode = 'TERM'
    assert csp.stop_mode == 'term'

    # Test: Stop mode setter, bad values
    with pytest.raises(ValueError):
        csp.stop_mode = 'terminate'

    with pytest.raises(ValueError):
        csp.stop_mode = -1


def test_cspgenericclass_status():
    """Tests CSPGenericClass._status"""
    from acceleratorAPI.exceptions import CSPInstanceException

    # Mock variables
    status = 'dummy_status'
    instance = None

    # Mock CSP class
    class DummyClass(get_dummy_csp_class()):
        """Dummy CSP"""
        def __init__(self):
            self._instance_id = None
            self._instance = None

        def __del__(self):
            """Do nothing"""

        def _get_status(self):
            """Returns fake result"""
            return status

        def _get_instance(self):
            """Return fake result"""
            return instance

    csp = DummyClass()

    # Test: No instance id
    with pytest.raises(CSPInstanceException):
        csp._status()

    # Test: instance id but no instance started
    csp._instance_id = 'dummy_id'
    with pytest.raises(CSPInstanceException):
        csp._status()

    # Test: instance id and instance started
    instance = 'dummy_instance'
    assert csp._status() == status
    assert csp._instance == instance


def test_cspgenericclass_start():
    """Tests CSPGenericClass.start"""
    from acceleratorAPI.exceptions import CSPException
    import acceleratorAPI._utilities as utl

    # Mock variables
    status = 'dummy_status'
    instance = 'dummy_instance'
    dummy_url = 'http://127.0.0.1'
    instance_id = 'dummy_id'
    raises_on_create_instance = False
    raises_on_start_instance = False
    raises_on_stop_instance = False
    raises_on_boot = False
    dummy_kwargs = {
        'region': 'dummy_region',
        'client_id': 'dummy_client_id'}

    # Mock CSP class
    class DummyClass(get_dummy_csp_class()):
        """Dummy CSP"""
        DOC_URL = 'dummy_csp_help'
        STATUS_RUNNING = status
        TIMEOUT = 0.0
        mark_credential_checked = False
        mark_key_pair_created = False
        mark_instance_created = False
        mark_instance_terminated = False
        mark_instance_started = False

        @staticmethod
        def _set_accelerator_requirements(*_, **__):
            """Tested separately"""

        def _check_credential(self):
            """Marks as executed"""
            self.mark_credential_checked = True

        def _init_key_pair(self):
            """Marks as executed, returns fake result"""
            self.mark_key_pair_created = True
            return True

        def _create_instance(self):
            """Marks as executed, simulate exception"""
            if raises_on_create_instance:
                # Exception with no message
                raise CSPException
            self.mark_instance_created = True

        def _terminate_instance(self):
            """Marks as executed, simulate exception"""
            if raises_on_stop_instance:
                raise CSPException
            self.mark_instance_terminated = True

        def _start_new_instance(self):
            """Marks as executed, simulate exception
            and returns fake result"""
            if raises_on_start_instance:
                # Exception with message
                raise CSPException('Error on start')
            self.mark_instance_started = True
            return instance, instance_id

        @staticmethod
        def _get_status():
            """Returns fake result"""
            return status

        @staticmethod
        def _get_instance():
            """Returns fake result"""
            return instance

        def _start_existing_instance(self, state):
            """Checks Argument and marks as executed"""
            assert state == status
            self.mark_instance_started = True

        @staticmethod
        def _get_public_ip():
            """Marks as executed"""
            return dummy_url

    # Mock check_url function
    def dummy_check_url(url, **_):
        """Checks argument and returns fake result"""
        assert url == dummy_url
        return not raises_on_boot

    utl_check_url = utl.check_url
    utl.check_url = dummy_check_url

    # Tests
    try:
        # Test: start from nothing with success
        csp = DummyClass(**dummy_kwargs)
        csp.start()
        assert csp._instance == instance
        assert csp.instance_id == instance_id
        assert csp.url == dummy_url
        assert csp.mark_credential_checked
        assert csp.mark_key_pair_created
        assert csp.mark_instance_created
        assert csp.mark_instance_started
        assert not csp.mark_instance_terminated

        # Test: Fail on create instance
        raises_on_create_instance = True
        csp = DummyClass(**dummy_kwargs)
        with pytest.raises(CSPException):
            csp.start()
        assert csp.mark_credential_checked
        assert csp.mark_key_pair_created
        assert not csp.mark_instance_created
        assert csp.mark_instance_terminated

        raises_on_create_instance = False

        # Test: Same, but also fail on stop
        # Case where no instance to stop, should
        # try to stop and fail silently
        raises_on_stop_instance = True
        raises_on_create_instance = True
        csp = DummyClass(**dummy_kwargs)
        with pytest.raises(CSPException) as exc_info:
            csp.start()
            assert csp.DOC_URL in exc_info
        assert not csp.mark_instance_created
        assert not csp.mark_instance_terminated

        raises_on_create_instance = False
        raises_on_stop_instance = False

        # Test: Fail on start instance
        raises_on_start_instance = True
        csp = DummyClass(**dummy_kwargs)
        with pytest.raises(CSPException) as exc_info:
            csp.start()
            assert csp.DOC_URL in exc_info
        assert csp.mark_credential_checked
        assert csp.mark_key_pair_created
        assert csp.mark_instance_created
        assert not csp.mark_instance_started
        assert csp.mark_instance_terminated

        raises_on_start_instance = False

        # Test: Fail on instance provisioning
        csp = DummyClass(**dummy_kwargs)
        csp.STATUS_RUNNING = 'bad_status'
        with pytest.raises(CSPException) as exc_info:
            csp.start()
            assert csp.DOC_URL in exc_info
        assert csp.mark_credential_checked
        assert csp.mark_key_pair_created
        assert csp.mark_instance_created
        assert csp.mark_instance_started
        assert csp.mark_instance_terminated

        # Test: Fail on boot instance
        raises_on_boot = True
        csp = DummyClass(**dummy_kwargs)
        with pytest.raises(CSPException):
            csp.start()
        assert csp.mark_credential_checked
        assert csp.mark_key_pair_created
        assert csp.mark_instance_created
        assert csp.mark_instance_started
        assert not csp.mark_instance_terminated

        raises_on_boot = False

        # Test: Start from an instance ID
        csp = DummyClass(region='dummy_region', instance_id=instance_id)
        csp.start()
        assert csp._instance == instance
        assert csp.instance_id == instance_id
        assert csp.url == dummy_url
        assert csp.mark_credential_checked
        assert not csp.mark_key_pair_created
        assert not csp.mark_instance_created
        assert csp.mark_instance_started
        assert not csp.mark_instance_terminated

        # Test: Start from an instance URL
        csp = DummyClass(region='dummy_region', instance_ip=dummy_url)
        csp.start()
        assert csp._url == dummy_url

        # Test: Start from an instance URL not reachable
        raises_on_boot = True
        csp = DummyClass(region='dummy_region', instance_ip=dummy_url)
        with pytest.raises(CSPException):
            csp.start()

        raises_on_boot = False

    # Restore check_url
    finally:
        utl.check_url = utl_check_url


def test_cspgenericclass_stop():
    """Tests CSPGenericClass.stop"""
    from acceleratorAPI.csp import CSPGenericClass

    # Mock variables
    instance = "dummy_instance"

    # Mock CSP class
    dummy_csp_class = get_dummy_csp_class()

    class DummyCSP(dummy_csp_class):
        """Dummy CSP"""
        stopped_mode = 'keep'
        class_stopped_mode = 'keep'

        def __init__(self, **kwargs):
            """Simulate already started instance"""
            dummy_csp_class.__init__(
                self, region='dummy_region',
                client_id='dummy_client_id', **kwargs)

            # Value like already started instance
            self._instance = instance
            self._url = 'http://127.0.0.1'
            self._instance_id = 'dummy_id'

        def _terminate_instance(self):
            """Marks as executed"""
            self.stopped_mode = 'term'
            DummyCSP.class_stopped_mode = 'term'

        def _pause_instance(self):
            """Marks as executed"""
            self.stopped_mode = 'stop'
            DummyCSP.class_stopped_mode = 'stop'

        def _get_instance(self):
            """Returns Fake result"""
            return instance

    # Test: Stop mode passed on instantiation
    for stop_mode in ('term', 'stop'):
        csp = DummyCSP(stop_mode=stop_mode)
        csp.stop()
        assert csp.stopped_mode == stop_mode

    # Test: Stop mode passed on stop
    for stop_mode in ('term', 'stop'):
        csp = DummyCSP()
        csp.stop(stop_mode)
        assert not csp._instance
        assert csp.stopped_mode == stop_mode

    # Test: Keep stop mode, don't stop
    csp = DummyCSP(stop_mode='keep')
    csp.stop()
    assert csp._instance

    csp = DummyCSP()
    csp.stop(stop_mode='keep')
    assert csp._instance

    # Test: Stop with no instance started
    instance = None
    csp = DummyCSP(stop_mode='term')
    csp.stop()
    assert csp.stopped_mode == 'keep'
    instance = 'dummy_instance'

    # Test: Auto-stops with context manager
    DummyCSP.class_stopped_mode = 'keep'
    with DummyCSP(stop_mode='term') as csp:
        # Checks __enter__ returned object
        assert isinstance(csp, CSPGenericClass)
    assert DummyCSP.class_stopped_mode == 'term'

    # Test: Auto-stops on garbage collection
    DummyCSP.class_stopped_mode = 'keep'
    DummyCSP(stop_mode='term')
    gc.collect()
    assert DummyCSP.class_stopped_mode == 'term'


def test_cspgenericclass_set_accelerator_requirements():
    """Tests CSPGenericClass._set_accelerator_requirements"""
    from acceleratorAPI.exceptions import CSPConfigurationException

    # Mock variables
    dummy_provider = 'dummy_provider'
    region = "dummy_region"
    image_id = "dummy_image_id"
    instance_type = "dummy_instance_type"
    config_env = "dummy_config_env"
    region_parameters = {'image': image_id, 'instancetype': instance_type}
    accelerator = "dummy_accelerator"
    accel_parameters = {region: region_parameters, 'accelerator': accelerator}

    # Mock Accelerator client

    class DummyClient:
        """Dummy accelerator client"""

        @staticmethod
        def get_requirements(provider):
            """Checks argument and returns fake result"""
            # Checks arguments
            assert provider == dummy_provider

            # Returns fake value
            return accel_parameters

    # Test: Everything is OK
    csp = get_dummy_csp_class()(
        region=region, client_id='dummy_client_id')
    csp._config_env = config_env
    csp._set_accelerator_requirements(accel_parameters=accel_parameters)
    assert csp._image_id == image_id
    assert csp._instance_type == instance_type
    assert csp.get_configuration_env() == config_env
    assert csp._accelerator == accelerator
    assert accelerator in csp._get_instance_name()

    # Test: Pass client
    csp = get_dummy_csp_class()(
        provider=dummy_provider, region=region, client_id='dummy_client_id')
    csp._config_env = config_env
    csp._set_accelerator_requirements(accel_client=DummyClient())
    assert csp._image_id == image_id
    assert csp._instance_type == instance_type
    assert csp.get_configuration_env() == config_env
    assert csp._accelerator == accelerator
    assert accelerator in csp._get_instance_name()

    # Test: Region not found
    accel_parameters = {'another_region': region_parameters, 'accelerator': accelerator}
    with pytest.raises(CSPConfigurationException):
        csp._set_accelerator_requirements(accel_parameters=accel_parameters)


def import_from_generic_test(provider, **kwargs):
    """
    Test to import a class from generic.

    Args:
        provider( str): CSP provider
        kwargs: Other args required
    """
    from acceleratorAPI.csp import CSPGenericClass
    CSPGenericClass(
        provider=provider, region='dummy_region',
        client_id='dummy_client_id', secret_id='dummy_secret_id',
        **kwargs)


def run_full_real_test_sequence(provider, environment,
                                use_full_images=False,
                                support_stop_restart=True):
    """Run common real tests for all CSP.

    Args:
        provider (str): CSP provider.
        environment (dict): Environment to use
        use_full_images (bool): If True, uses full
            images with host application that provides
            HTTP access.
        support_stop_restart (bool): If True support pause instance
            and restart.
    """
    from acceleratorAPI.configuration import Configuration

    # Skip if no correct configuration with this provider
    config = Configuration()
    if not config.has_csp_credential():
        pytest.skip('No CSP credentials')

    if config.get_default('csp', 'provider') != provider:
        pytest.skip('No configuration for %s.' % provider)

    elif config.get_default('csp', 'region') not in environment:
        pytest.skip("No configuration for '%s' region on %s." %
                    (config.get_default('csp', 'region'), provider))

    # Enable logger
    from acceleratorAPI import get_logger
    get_logger(stdout=True)

    # Add accelerator to environment
    environment['accelerator'] = 'acceleratorAPI_testing'

    # Mock instance URL check
    # Since used basic image don't provide HTTP access
    if not use_full_images:
        import acceleratorAPI._utilities

        def dummy_check_url(_, timeout=0.0, **__):
            """Don't check URL, only waits if timeout and returns True"""
            if timeout:
                time.sleep(60)
            return True

        utilities_check_url = acceleratorAPI._utilities.check_url
        acceleratorAPI._utilities.check_url = dummy_check_url

    # Tests:
    from acceleratorAPI.csp import CSPGenericClass

    try:
        # Start and terminate
        print('Test: Start and terminate')
        with CSPGenericClass(config=config, stop_mode='term') as csp:
            csp.start(accel_parameters=environment)

        gc.collect()

        # Start and stop, then terminate
        # Also check getting instance handle with ID
        if support_stop_restart:
            print('Test: Start and stop')
            with CSPGenericClass(config=config, stop_mode='stop') as csp:
                csp.start(accel_parameters=environment)
                instance_id = csp.instance_id

            gc.collect()

            print('Test: Start from stopped and terminate')
            with CSPGenericClass(config=config, instance_id=instance_id,
                                 stop_mode='term') as csp:
                csp.start()

            gc.collect()

        # Start and keep, then
        # Also check getting instance handle with URL
        print('Test: Start and keep')
        with CSPGenericClass(config=config, stop_mode='keep') as csp:
            csp.start(accel_parameters=environment)
            instance_ip = csp.url
            instance_id = csp.instance_id

        gc.collect()

        print('Test: Reuse with instance IP')
        with CSPGenericClass(config=config, instance_ip=instance_ip) as csp:
            csp.start()

        gc.collect()

        print('Test: Reuse with instance ID and terminate')
        with CSPGenericClass(config=config, instance_id=instance_id,
                             stop_mode='term') as csp:
            csp.start()

    # Restore check_url
    finally:
        if not use_full_images:
            acceleratorAPI._utilities.check_url = utilities_check_url
