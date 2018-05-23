# coding=utf-8
"""acceleratorAPI.csp tests"""
import gc
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
    kwargs = {'region': 'region', 'project_id': 'project_id',
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
        CSP_NAME = 'Dummy'

        def _get_instance_public_ip(self):
            """Dummy method"""

        def _get_instance_private_ip(self):
            """Dummy method"""

        def check_credential(self):
            """Dummy method"""

        def _get_instance_status(self):
            """Dummy method"""

        def _get_instance(self):
            """Dummy method"""

        def _init_ssh_key(self):
            """Dummy method"""

        def _create_instance(self):
            """Dummy method"""

        def _start_new_instance(self):
            """Dummy method"""

        def _start_existing_instance(self, **kwargs):
            """Dummy method"""

        def _wait_instance_ready(self):
            """Dummy method"""

        def _terminate_instance(self):
            """Dummy method"""

        def _pause_instance(self):
            """Dummy method"""

        def _read_accelerator_parameters(self, **kwargs):
            """Dummy method"""

    return BaseDummyClass


def test_cspgenericclass_properties():
    """Tests CSPGenericClass properties"""
    from acceleratorAPI.csp import KEEP, TERM
    from acceleratorAPI.exceptions import CSPInstanceException

    # Mock variables
    provider = 'dummy_provider'
    instance_ip = 'dummy_public_ip'
    instance_private_ip = 'dummy_private_ip'
    instance_url = 'http://127.0.0.1'
    instance_id = 'dummy_instance_id'
    stop_mode = KEEP
    region = 'dummy_region'

    # Mock CSP class
    class DummyClass(get_dummy_csp_class()):
        """Dummy CSP"""

        def _get_instance_public_ip(self):
            """Returns fake result"""
            return instance_ip

        def _get_instance_private_ip(self):
            """Returns fake result"""
            return instance_private_ip

    csp = DummyClass(
        provider=provider, instance_url=instance_url,
        instance_id=instance_id, stop_mode=stop_mode,
        region=region)
    csp._instance = 'dummy_instance'

    # Test: properties values
    assert csp.provider == provider
    assert csp.instance_ip == instance_ip
    assert csp.instance_private_ip == instance_private_ip
    assert csp.instance_url == instance_url
    assert csp.instance_id == instance_id
    assert csp.stop_mode == stop_mode

    # Test: Information property
    # 'not_exists' tests case where a value is not defined on class
    # (Example if specific only to some CSP subclasses). But we
    # don't want property crash in this case, only return
    # a dict without not existing values
    csp._INFO_NAMES.add('not_exists')
    info = csp.instance_info
    for name in {
            'provider', 'instance_ip',
            'instance_private_ip', 'instance_url',
            'instance_id', 'region', 'stop_mode'}:
        assert info[name] == locals()[name]
    assert 'not_exists' not in info

    # Test: properties if no instance
    csp._instance = None
    with pytest.raises(CSPInstanceException):
        csp.instance_ip

    with pytest.raises(CSPInstanceException):
        csp.instance_private_ip

    # Test: Stop mode setter, no change if no value set
    csp.stop_mode = None
    assert csp.stop_mode == stop_mode

    # Test: Stop mode setter, set value as int
    csp.stop_mode = 0
    assert csp.stop_mode == TERM

    # Test: Stop mode setter, set value as str
    csp.stop_mode = '0'
    assert csp.stop_mode == TERM

    # Test: Stop mode setter, bad values
    with pytest.raises(ValueError):
        csp.stop_mode = 'KEEP'

    with pytest.raises(ValueError):
        csp.stop_mode = -1


def test_cspgenericclass_instance_status():
    """Tests CSPGenericClass.instance_status"""
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

        def _get_instance_status(self):
            """Returns fake result"""
            return status

        def _get_instance(self):
            """Return fake result"""
            return instance

    csp = DummyClass()

    # Test: No instance id
    with pytest.raises(CSPInstanceException):
        csp.instance_status()

    # Test: instance id but no instance started
    csp._instance_id = 'dummy_id'
    with pytest.raises(CSPInstanceException):
        csp.instance_status()

    # Test: instance id and instance started
    instance = 'dummy_instance'
    assert csp.instance_status() == status
    assert csp._instance == instance


def test_cspgenericclass_start_instance():
    """Tests CSPGenericClass.start_instance"""
    from acceleratorAPI.exceptions import CSPException
    import acceleratorAPI._utilities as utl

    # Mock variables
    status = 'dummy_status'
    instance = 'dummy_instance'
    instance_url = 'http://127.0.0.1'
    instance_id = 'dummy_id'
    raises_on_create_instance = False
    raises_on_start_instance = False
    raises_on_instance_provisioning = False
    raises_on_stop_instance = False
    raises_on_boot = False

    # Mock CSP class
    class DummyClass(get_dummy_csp_class()):
        """Dummy CSP"""
        CSP_HELP_URL = 'dummy_csp_help'
        mark_credential_checked = False
        mark_ssh_key_created = False
        mark_instance_created = False
        mark_instance_terminated = False
        mark_instance_started = False
        mark_instance_ready = False

        def check_credential(self):
            """Marks as executed"""
            self.mark_credential_checked = True

        def _init_ssh_key(self):
            """Marks as executed, returns fake result"""
            self.mark_ssh_key_created = True
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
        def _get_instance_status():
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

        def _wait_instance_ready(self):
            """Marks as executed, simulate exception"""
            if raises_on_instance_provisioning:
                # Exception with message
                raise CSPException('Error on start')
            self.mark_instance_ready = True

        @staticmethod
        def _get_instance_public_ip():
            """Marks as executed"""
            return instance_url

    # Mock check_url function
    def dummy_check_url(url, **_):
        """Checks argument and returns fake result"""
        assert url == instance_url
        return not raises_on_boot

    utl_check_url = utl.check_url
    utl.check_url = dummy_check_url

    # Tests
    try:
        # Test: start from nothing with success
        csp = DummyClass(region='dummy_region')
        csp.start_instance()
        assert csp._instance == instance
        assert csp.instance_id == instance_id
        assert csp.instance_url == instance_url
        assert csp.mark_credential_checked
        assert csp.mark_ssh_key_created
        assert csp.mark_instance_created
        assert csp.mark_instance_started
        assert csp.mark_instance_ready
        assert not csp.mark_instance_terminated

        # Test: Fail on create instance
        raises_on_create_instance = True
        csp = DummyClass(region='dummy_region')
        with pytest.raises(CSPException):
            csp.start_instance()
        assert csp.mark_credential_checked
        assert csp.mark_ssh_key_created
        assert not csp.mark_instance_created
        assert csp.mark_instance_terminated

        raises_on_create_instance = False

        # Test: Same, but also fail on stop
        # Case where no instance to stop, should
        # try to stop and fail silently
        raises_on_stop_instance = True
        raises_on_create_instance = True
        csp = DummyClass(region='dummy_region')
        with pytest.raises(CSPException) as exc_info:
            csp.start_instance()
            assert csp.CSP_HELP_URL in exc_info
        assert not csp.mark_instance_created
        assert not csp.mark_instance_terminated

        raises_on_create_instance = False
        raises_on_stop_instance = False

        # Test: Fail on start instance
        raises_on_start_instance = True
        csp = DummyClass(region='dummy_region')
        with pytest.raises(CSPException) as exc_info:
            csp.start_instance()
            assert csp.CSP_HELP_URL in exc_info
        assert csp.mark_credential_checked
        assert csp.mark_ssh_key_created
        assert csp.mark_instance_created
        assert not csp.mark_instance_started
        assert csp.mark_instance_terminated

        raises_on_start_instance = False

        # Test: Fail on instance provisioning
        raises_on_instance_provisioning = True
        with pytest.raises(CSPException) as exc_info:
            csp.start_instance()
            assert csp.CSP_HELP_URL in exc_info
        assert csp.mark_credential_checked
        assert csp.mark_ssh_key_created
        assert csp.mark_instance_created
        assert csp.mark_instance_started
        assert not csp.mark_instance_ready
        assert csp.mark_instance_terminated
        raises_on_instance_provisioning = False

        # Test: Fail on boot instance
        raises_on_boot = True
        csp = DummyClass(region='dummy_region')
        with pytest.raises(CSPException):
            csp.start_instance()
        assert csp.mark_credential_checked
        assert csp.mark_ssh_key_created
        assert csp.mark_instance_created
        assert csp.mark_instance_started
        assert not csp.mark_instance_terminated

        raises_on_boot = False

        # Test: Start from an instance ID
        csp = DummyClass(region='dummy_region', instance_id=instance_id)
        csp.start_instance()
        assert csp._instance == instance
        assert csp.instance_id == instance_id
        assert csp.instance_url == instance_url
        assert csp.mark_credential_checked
        assert not csp.mark_ssh_key_created
        assert not csp.mark_instance_created
        assert csp.mark_instance_started
        assert csp.mark_instance_ready
        assert not csp.mark_instance_terminated

        # Test: Start from an instance URL
        csp = DummyClass(region='dummy_region', instance_url=instance_url)
        csp.start_instance()
        assert csp.instance_url == instance_url

        # Test: Start from an instance URL not reachable
        raises_on_boot = True
        csp = DummyClass(region='dummy_region', instance_url=instance_url)
        with pytest.raises(CSPException):
            csp.start_instance()

        raises_on_boot = False

    # Restore check_url
    finally:
        utl.check_url = utl_check_url


def test_cspgenericclass_stop_instance():
    """Tests CSPGenericClass.stop_instance"""
    from acceleratorAPI.csp import KEEP, TERM, STOP, CSPGenericClass

    # Mock variables
    instance = "dummy_instance"

    # Mock CSP class
    dummy_csp_class = get_dummy_csp_class()

    class DummyCSP(dummy_csp_class):
        """Dummy CSP"""
        stopped_mode = KEEP
        class_stopped_mode = KEEP

        def __init__(self, **kwargs):
            """Simulate already started instance"""
            dummy_csp_class.__init__(self, region='dummy_region', **kwargs)

            # Value like already started instance
            self._instance = instance
            self._instance_url = 'http://127.0.0.1'
            self._instance_id = 'dummy_id'

        def _terminate_instance(self):
            """Marks as executed"""
            self.stopped_mode = TERM
            DummyCSP.class_stopped_mode = TERM

        def _pause_instance(self):
            """Marks as executed"""
            self.stopped_mode = STOP
            DummyCSP.class_stopped_mode = STOP

        def _get_instance(self):
            """Returns Fake result"""
            return instance

    # Test: Stop mode passed on instantiation
    for stop_mode in (TERM, STOP):
        csp = DummyCSP(stop_mode=stop_mode)
        csp.stop_instance()
        assert csp.stopped_mode == stop_mode

    # Test: Stop mode passed on stop_instance
    for stop_mode in (TERM, STOP):
        csp = DummyCSP()
        csp.stop_instance(stop_mode)
        assert csp.stopped_mode == stop_mode

    # Test: Keep stop mode, don't stop but warn user
    with warnings.catch_warnings():
        warnings.simplefilter("always")

        csp = DummyCSP(stop_mode=KEEP)
        with pytest.warns(Warning):
            csp.stop_instance()

        csp = DummyCSP()
        with pytest.warns(Warning):
            csp.stop_instance(stop_mode=KEEP)

    # Test: Stop with no instance started
    instance = None
    csp = DummyCSP(stop_mode=TERM)
    csp.stop_instance()
    assert csp.stopped_mode == KEEP
    instance = 'dummy_instance'

    # Test: Auto-stops with context manager
    DummyCSP.class_stopped_mode = KEEP
    with DummyCSP(stop_mode=TERM) as csp:
        # Checks __enter__ returned object
        assert isinstance(csp, CSPGenericClass)
    assert DummyCSP.class_stopped_mode == TERM

    # Test: Auto-stops on garbage collection
    DummyCSP.class_stopped_mode = KEEP
    DummyCSP(stop_mode=TERM)
    gc.collect()
    assert DummyCSP.class_stopped_mode == TERM


def test_cspgenericclass_set_accelerator_requirements():
    """Tests CSPGenericClass.set_accelerator_requirements"""
    from acceleratorAPI.exceptions import CSPConfigurationException

    # Mock variables
    region = "dummy_region"
    region_parameters = "dummy_parameters"
    accelerator = "dummy_accelerator"
    image_id = "dummy_image_id"
    instance_type = "dummy_instance_type"
    config_env = "dummy_config_env"

    # Mock CSP class
    class DummyCSP(get_dummy_csp_class()):
        """Dummy CSP"""

        @staticmethod
        def _read_accelerator_parameters(parameters):
            """Checks arguments and returns fake result"""
            # Checks arguments
            assert parameters == region_parameters

            # Returns result
            return image_id, instance_type, config_env

    csp = DummyCSP(region=region)

    # Test: get_configuration_env returns default empty value
    assert csp.get_configuration_env() == csp._config_env == {}

    # Test: Everything is OK
    accel_parameters = {region: region_parameters, 'accelerator': accelerator}
    csp.set_accelerator_requirements(accel_parameters)
    assert csp._image_id == image_id
    assert csp._instance_type == instance_type
    assert csp.get_configuration_env() == config_env
    assert csp._accelerator == accelerator

    # Test: Region not found
    accel_parameters = {'another_region': region_parameters, 'accelerator': accelerator}
    with pytest.raises(CSPConfigurationException):
        csp.set_accelerator_requirements(accel_parameters)


def run_full_real_test_sequence(provider):
    """Run common real tests for all CSP.

    Args:
        provider (str): CSP provider.
    """
    from acceleratorAPI.configuration import Configuration

    # Skip if no configuration with this provider
    config = Configuration()
    if config.get_default('csp', 'provider') != provider:
        pytest.skip('No configuration for %s.' % provider)

    from acceleratorAPI.csp import CSPGenericClass, TERM, STOP, KEEP

    # Test: Start and terminate
    with CSPGenericClass(config=config, stop_mode=TERM) as csp:
        csp.start_instance()

    # Test: Start and stop, then terminate
    # Also check getting instance handle with ID
    with CSPGenericClass(config=config, stop_mode=STOP) as csp:
        csp.start_instance()
        instance_id = csp.instance_id

    with CSPGenericClass(config=config, instance_id=instance_id, stop_mode=TERM) as csp:
        csp.start_instance()

    # Test: Start and keep, then
    # Also check getting instance handle with URL
    with CSPGenericClass(config=config, stop_mode=KEEP) as csp:
        csp.start_instance()
        instance_url = csp.instance_url

    with CSPGenericClass(config=config, instance_url=instance_url, stop_mode=TERM) as csp:
        csp.start_instance()
