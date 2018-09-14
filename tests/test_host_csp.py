# coding=utf-8
"""apyfal.host._csp tests"""
from copy import deepcopy
from datetime import datetime
import gc
import os
import time

import pytest


def test_csphost_new_init():
    """Tests Host.__new__ and Host.__init__"""
    from apyfal.configuration import Configuration
    from apyfal.host import Host
    from apyfal.host._csp import CSPHost
    from apyfal.host.ovh import OVHHost
    from apyfal.exceptions import HostConfigurationException

    # Mock arguments and configuration
    # Note that host_type is not specified here
    config = Configuration()
    try:
        for section in list(config._sections):
            if section.startswith('host'):
                del config._sections[section]
    except KeyError:
        pass
    kwargs = {'region': 'region', 'project_id': 'project_id',
              'client_id': 'client_id',
              'auth_url': 'auth_url', 'interface': 'interface',
              'config': config}

    # Test: Existing CSP class and module
    assert isinstance(Host(host_type="OVH", **kwargs), OVHHost)

    # Test: Not existing CSP module
    with pytest.raises(HostConfigurationException):
        Host(host_type="no_existing_csp")

    # Test: Existing CSP module, with no valid class
    with pytest.raises(HostConfigurationException):
        Host(host_type="_csp")

    # Test: direct instantiation of subclass without specify host_type
    host = OVHHost(**kwargs)

    # Test: repr
    assert repr(host) == str(host)

    # Test: Instantiation with missing mandatory arguments
    with pytest.raises(HostConfigurationException):
        Host(host_type="OVH", config=config)

    kwargs_no_client_id = kwargs.copy()
    del kwargs_no_client_id['client_id']
    with pytest.raises(HostConfigurationException):
        Host(host_type="OVH", **kwargs_no_client_id)

    # Test: Abstract class
    class UncompletedCSP(CSPHost):
        """Uncompleted CSP class"""

    with pytest.raises(TypeError):
        UncompletedCSP()


def get_dummy_csp_class():
    """
    Returns a base dummy subclass of Host

    Returns:
        apyfal.host._csp.CSPHost subclass
    """
    from apyfal.host._csp import CSPHost

    class BaseDummyClass(CSPHost):
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

        def _init_security_group(self):
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


def test_csphost_properties():
    """Tests Host properties"""
    from apyfal.exceptions import HostRuntimeException

    # Mock variables
    host_type = 'dummy_host_type'
    public_ip = 'dummy_public_ip'
    private_ip = 'dummy_private_ip'
    url = 'http://127.0.0.1'
    instance_id = 'dummy_instance_id'
    stop_mode = 'keep'
    region = 'dummy_region'
    key_pair = 'dummy_key_pair'
    ssl_cert_crt = 'dummy_ssl_cert_crt'

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
        host_type=host_type,
        instance_id=instance_id, stop_mode=stop_mode,
        region=region, key_pair=key_pair, ssl_cert_crt=ssl_cert_crt)
    csp._instance = 'dummy_instance'
    csp._url = 'http://127.0.0.1'

    # Test: properties values
    assert csp.host_type == host_type
    assert csp.public_ip == public_ip
    assert csp.host_ip == public_ip
    assert csp.private_ip == private_ip
    assert csp.url == url
    assert csp.instance_id == instance_id
    assert csp.stop_mode == stop_mode
    assert csp.key_pair == key_pair
    assert csp.ssl_cert_crt == ssl_cert_crt

    # Test: Use private IP
    csp_private = DummyClass(
        host_type=host_type,
        instance_id=instance_id, stop_mode=stop_mode,
        region=region, key_pair=key_pair, use_private_ip=True)
    csp_private._instance = 'dummy_instance'
    csp_private._url = 'http://127.0.0.1'

    assert csp_private.public_ip == public_ip
    assert csp_private.host_ip == private_ip
    assert csp_private.private_ip == private_ip

    # Test: Information property
    # 'not_exists' tests case where a value is not defined on class
    # (Example if specific only to some CSP subclasses). But we
    # don't want property crash in this case, only return
    # a dict without not existing values
    csp._INFO_NAMES.add('not_exists')
    info = csp.info
    for name in {
        'host_type', 'public_ip',
        'private_ip', 'url',
        'instance_id', 'region', 'stop_mode'}:
        assert info[name] == locals()[name]
    assert 'not_exists' not in info

    # Test: properties if no instance
    csp._instance = None
    with pytest.raises(HostRuntimeException):
        csp.public_ip

    with pytest.raises(HostRuntimeException):
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


def test_csphost_status():
    """Tests Host._status"""
    from apyfal.exceptions import HostRuntimeException

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
    with pytest.raises(HostRuntimeException):
        csp._status()

    # Test: instance id but no instance started
    csp._instance_id = 'dummy_id'
    with pytest.raises(HostRuntimeException):
        csp._status()

    # Test: instance id and instance started
    instance = 'dummy_instance'
    assert csp._status() == status
    assert csp._instance == instance


def test_csphost_start():
    """Tests Host.start"""
    from apyfal.exceptions import HostException
    import apyfal._utilities as utl

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
    base_class = get_dummy_csp_class()

    class DummyClass(base_class):
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
                raise HostException
            self.mark_instance_created = True
            base_class._create_instance(self)

        def _terminate_instance(self):
            """Marks as executed, simulate exception"""
            if raises_on_stop_instance:
                raise HostException
            self.mark_instance_terminated = True

        def _start_new_instance(self):
            """Marks as executed, simulate exception
            and returns fake result"""
            if raises_on_start_instance:
                # Exception with message
                raise HostException('Error on start')
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
        with pytest.raises(HostException):
            csp.start()
        assert csp.mark_credential_checked
        assert not csp.mark_instance_created
        assert csp.mark_instance_terminated

        raises_on_create_instance = False

        # Test: Same, but also fail on stop
        # Case where no instance to stop, should
        # try to stop and fail silently
        raises_on_stop_instance = True
        raises_on_create_instance = True
        csp = DummyClass(**dummy_kwargs)
        with pytest.raises(HostException) as exc_info:
            csp.start()
            assert csp.DOC_URL in exc_info
        assert not csp.mark_instance_created
        assert not csp.mark_instance_terminated

        raises_on_create_instance = False
        raises_on_stop_instance = False

        # Test: Fail on start instance
        raises_on_start_instance = True
        csp = DummyClass(**dummy_kwargs)
        with pytest.raises(HostException) as exc_info:
            csp.start()
            assert csp.DOC_URL in exc_info
        assert csp.mark_credential_checked
        assert csp.mark_key_pair_created
        assert csp.mark_instance_created
        assert not csp.mark_instance_started
        assert csp.mark_instance_terminated

        raises_on_start_instance = False

        # Test: Fail on instance provisioning
        # by timeout
        csp = DummyClass(**dummy_kwargs)
        status = 'bad_status'
        with pytest.raises(HostException) as exc_info:
            csp.start()
            assert csp.DOC_URL in exc_info
        assert csp.mark_credential_checked
        assert csp.mark_key_pair_created
        assert csp.mark_instance_created
        assert csp.mark_instance_started
        assert csp.mark_instance_terminated

        # Test: Fail on instance provisioning
        # by error
        csp = DummyClass(**dummy_kwargs)
        status = csp.STATUS_ERROR
        with pytest.raises(HostException):
            csp.start()
        status = csp.STATUS_RUNNING

        # Test: Fail on boot instance
        raises_on_boot = True
        csp = DummyClass(**dummy_kwargs)
        with pytest.raises(HostException):
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

        # Test: Start with already existing URL
        csp.start()
        assert csp._url == dummy_url

        # Test: Start with already existing URL but not reachable
        raises_on_boot = True
        with pytest.raises(HostException):
            csp.start()

        raises_on_boot = False

    # Restore check_url
    finally:
        utl.check_url = utl_check_url


def test_csphost_stop(tmpdir):
    """Tests Host.stop"""
    from apyfal.host import Host
    from apyfal.exceptions import HostRuntimeException

    # Mock variables
    instance = "dummy_instance"
    url = 'http://127.0.0.1'

    # Mock CSP class
    dummy_csp_class = get_dummy_csp_class()
    raise_on_status = False

    class DummyHost(dummy_csp_class):
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
            self._url = url
            self._instance_id = 'dummy_id'

        def _terminate_instance(self):
            """Marks as executed"""
            self.stopped_mode = 'term'
            DummyHost.class_stopped_mode = 'term'

        def _pause_instance(self):
            """Marks as executed"""
            self.stopped_mode = 'stop'
            DummyHost.class_stopped_mode = 'stop'

        def _get_instance(self):
            """Returns Fake result"""
            return instance

        def _status(self):
            """Raises exception"""
            if raise_on_status:
                raise HostRuntimeException

    # Test: Stop mode passed on instantiation
    for stop_mode in ('term', 'stop'):
        csp = DummyHost(stop_mode=stop_mode)
        csp.stop()
        assert csp.stopped_mode == stop_mode

    # Test: Stop mode passed on stop
    for stop_mode in ('term', 'stop'):
        csp = DummyHost()
        csp.stop(stop_mode)
        assert not csp._instance
        assert csp.stopped_mode == stop_mode

    # Test: Keep stop mode, don't stop
    csp = DummyHost(stop_mode='keep')
    csp.stop()
    assert csp._instance

    csp = DummyHost()
    csp.stop(stop_mode='keep')
    assert csp._instance

    config = tmpdir.join('dummy_accelerator.conf')
    config.write('[host]\nstop_mode=keep')
    csp = DummyHost(config=str(config))
    csp.stop()
    assert csp._instance

    # Test: Stop with no instance started
    csp = DummyHost(stop_mode='term')
    csp._instance_id = None
    csp.stop()
    assert csp.url == url
    assert csp.stopped_mode == 'keep'

    raise_on_status = True
    csp = DummyHost(stop_mode='term')
    csp.stop()
    assert csp.url == url
    assert csp.stopped_mode == 'keep'
    raise_on_status = False

    # Test: Auto-stops with context manager
    DummyHost.class_stopped_mode = 'keep'
    with DummyHost(stop_mode='term') as csp:
        # Checks __enter__ returned object
        assert isinstance(csp, Host)
    assert DummyHost.class_stopped_mode == 'term'

    # Test: Auto-stops on garbage collection
    DummyHost.class_stopped_mode = 'keep'
    DummyHost(stop_mode='term')
    gc.collect()
    assert DummyHost.class_stopped_mode == 'term'


def test_csphost_set_accelerator_requirements():
    """Tests Host._set_accelerator_requirements"""
    from apyfal.exceptions import HostConfigurationException
    from apyfal.configuration import Configuration

    # Mock variables
    dummy_host_type = 'dummy_host_type'
    region = "dummy_region"
    image_id = "dummy_image_id"
    instance_type = "dummy_instance_type"
    config_env = {"dummy_config_env": None}
    region_parameters = {'image': image_id, 'instancetype': instance_type}
    region_parameters.update(config_env)
    dummy_accelerator = "dummy_accelerator"
    accel_parameters = {region: region_parameters,
                        'accelerator': dummy_accelerator}

    # Mock Accelerator client

    def get_host_requirements(_, host_type, accelerator):
        """Checks argument and returns fake result"""
        # Checks arguments
        assert host_type == dummy_host_type
        assert accelerator == dummy_accelerator

        # Returns fake value
        return deepcopy(accel_parameters)

    configuration_get_host_requirements = Configuration.get_host_requirements
    Configuration.get_host_requirements = get_host_requirements

    try:
        # Test: Everything is OK
        csp = get_dummy_csp_class()(
            region=region, client_id='dummy_client_id')
        csp._set_accelerator_requirements(
            accel_parameters=deepcopy(accel_parameters))
        assert csp._image_id == image_id
        assert csp._instance_type == instance_type
        assert csp.get_configuration_env() == config_env
        assert csp._accelerator == dummy_accelerator
        assert dummy_accelerator in csp._get_host_name()
        assert dummy_accelerator in csp.host_name

        # Test: Pass accelerator and custom FPGA image
        csp = get_dummy_csp_class()(
            host_type=dummy_host_type, region=region,
            client_id='dummy_client_id')
        csp._config_env = config_env
        csp._set_accelerator_requirements(accelerator=dummy_accelerator)
        assert csp._image_id == image_id
        assert csp._instance_type == instance_type
        assert csp.get_configuration_env() == config_env
        assert csp._accelerator == dummy_accelerator
        assert dummy_accelerator in csp._get_host_name()

        # Test pass environment parameters
        new_config_env = config_env.copy()
        new_config_env['AGFI'] = new_config_env['fpgaimage'] = 'fpgaimage'
        assert csp.get_configuration_env(AGFI='fpgaimage') == new_config_env
        new_config_env = config_env.copy()
        new_config_env['param'] = 'param'
        assert csp.get_configuration_env(param='param') == new_config_env

        # Test: Region not found
        accel_parameters = {'another_region': region_parameters,
                            'accelerator': dummy_accelerator}
        with pytest.raises(HostConfigurationException):
            csp._set_accelerator_requirements(accel_parameters=accel_parameters)

    # Revert configuration method
    finally:
        Configuration.get_host_requirements = \
            configuration_get_host_requirements


def import_from_generic_test(host_type, **kwargs):
    """
    Test to import a class from generic.

    Args:
        host_type( str): CSP host_type
        kwargs: Other args required
    """
    from apyfal.host import Host
    Host(
        host_type=host_type, region='dummy_region',
        client_id='dummy_client_id', secret_id='dummy_secret_id',
        **kwargs)


def run_full_real_test_sequence(host_type, environment,
                                use_full_images=False):
    """Run common real tests for all CSP.

    Args:
        host_type (str): CSP host_type.
        environment (dict): Environment to use
        use_full_images (bool): If True, uses full
            images with host application that provides
            HTTP access.
    """
    from apyfal.configuration import Configuration
    from apyfal.exceptions import AcceleratorException
    from apyfal import iter_accelerators

    # Skip if no correct configuration with this host_type
    config = Configuration()

    if config['host']['host_type'] != host_type:
        config['host']['host_type'] = host_type
        try:
            del config['host']['client_id']
        except KeyError:
            pass
        try:
            del config['host']['secret_id']
        except KeyError:
            pass

    section = config['host.%s' % host_type]
    if not section['client_id'] or not section['secret_id']:
        pytest.skip('No configuration for %s.' % host_type)

    elif section['region'] not in environment:
        pytest.skip("No configuration for '%s' region on %s." %
                    (section['region'], host_type))

    # Enable logger
    from apyfal import get_logger
    get_logger(stdout=True)

    # Add accelerator to environment
    environment['accelerator'] = 'apyfal_testing'
    config['host']['host_name_prefix'] = datetime.now().strftime('test%H%M%S')

    # Mock instance URL check
    # Since used basic image don't provide HTTP access
    if not use_full_images:
        import apyfal._utilities

        def dummy_check_url(_, timeout=0.0, **__):
            """Don't check URL, only waits if timeout and returns True"""
            if timeout:
                time.sleep(60)
            return True

        utilities_check_url = apyfal._utilities.check_url
        apyfal._utilities.check_url = dummy_check_url

    # Tests:
    from apyfal.host import Host
    instance_id_term = None
    instance_id_stop = None
    instance_id_keep = None

    try:
        # Start and terminate
        print('Test: Start and terminate')
        with Host(config=config, stop_mode='term') as csp_term:
            csp_term.start(accel_parameters=environment)
            instance_id_term = csp_term.instance_id

        # Start and stop, then terminate
        # Also check getting instance handle with ID
        print('Test: Start and stop')
        with Host(config=config, stop_mode='stop') as csp_stop:
            csp_stop.start(accel_parameters=environment)
            instance_id_stop = csp_stop.instance_id

        print('Test: Start from stopped and terminate')
        with Host(config=config, instance_id=instance_id_stop,
                  stop_mode='term') as csp:
            csp.start(accel_parameters=environment)
            assert csp.instance_id == instance_id_stop

        # Start and keep, then
        # Also check getting instance handle with URL
        print('Test: Start and keep')
        with Host(config=config, stop_mode='keep') as csp_keep:
            csp_keep.start(accel_parameters=environment)
            instance_id_keep = csp_keep.instance_id
            instance_url_keep = csp_keep.url

        print('Test: Reuse with instance IP/URL')
        with Host(config=config, host_ip=instance_url_keep) as csp:
            csp.start(accel_parameters=environment)
            assert csp.url == instance_url_keep

        print('Test: Reuse with instance ID and terminate')
        with Host(config=config, instance_id=instance_id_keep,
                  stop_mode='term') as csp:
            csp.start(accel_parameters=environment)
            assert csp.instance_id == instance_id_keep

    # Restore check_url
    finally:
        if not use_full_images:
            apyfal._utilities.check_url = utilities_check_url

        # Stops all instances
        time.sleep(5)
        for accelerator in iter_accelerators(config=config):
            instance_id = None
            try:
                instance_id = accelerator.host.instance_id
                accelerator.stop('term')
            except AcceleratorException:
                pass
            assert instance_id not in (instance_id_term,
                                       instance_id_stop,
                                       instance_id_keep)


def test_csphost_user_data(tmpdir):
    """Tests Host._user_data"""
    from apyfal.configuration import Configuration
    from apyfal.exceptions import HostConfigurationException

    # Mock CSP class
    class DummyCSP(get_dummy_csp_class()):
        """Dummy CSP"""
        _SSL_CERT_HOME_DIR = str(tmpdir.join('tmp_certificates'))

        @property
        def host_name(self):
            """Return fake result"""
            return 'host_name'

        def _get_instance(self):
            """Do nothing"""

        def _status(self):
            """Do nothing"""

    config_content = ("[dummy]\n"
                      "dummy1 = dummy1\n"
                      "dummy2 = dummy2\n")
    config_file = tmpdir.join('dummy.conf')
    config_file.write(config_content)
    config = Configuration(str(config_file))

    script_content = ("#!/usr/bin/env bash\n"
                      "script line 1\n"
                      "script line 2")
    script_file = tmpdir.join('dummy.sh')
    script_file.write(script_content)

    ssl_crt_content = "public_key"
    ssl_crt_file = tmpdir.join('dummy.crt')
    ssl_crt_file.write(ssl_crt_content)

    ssl_key_content = "private_key"
    ssl_key_file = tmpdir.join('dummy.key')
    ssl_key_file.write(ssl_key_content)

    # No user data
    assert DummyCSP(
        client_id='client_id', secret_id='secret_id',
        region='region')._user_data is None

    # Get user data
    user_data = DummyCSP(
        client_id='client_id', secret_id='secret_id',
        region='region', init_config=config,
        init_script=str(script_file))._user_data.decode()

    # Check shebang
    assert user_data.count('#!') == 1

    # Check configuration file presence
    for line in config_content.splitlines():
        assert line in user_data

    # Check script file presence
    for line in script_content.splitlines()[1:]:
        assert line in user_data

    # Check path
    assert DummyCSP._HOME in user_data

    # Certificate
    user_data = DummyCSP(
        client_id='client_id', secret_id='secret_id',
        region='region', ssl_cert_crt=str(ssl_crt_file),
        ssl_cert_key=str(ssl_key_file))._user_data.decode()

    assert ssl_key_content in user_data
    assert ssl_crt_content in user_data
    assert DummyCSP._SSL_CERT_CRT in user_data
    assert DummyCSP._SSL_CERT_KEY in user_data

    # Generated certificate
    user_data = DummyCSP(
        client_id='client_id', secret_id='secret_id',
        region='region', ssl_cert_crt=str(ssl_crt_file),
        ssl_cert_key=str(ssl_key_file),
        ssl_cert_generate=True)._user_data.decode()

    assert ssl_crt_file.read_text('utf-8') in user_data
    assert ssl_key_file.read_text('utf-8') in user_data

    # Generated temporary certificate
    csp = DummyCSP(
        client_id='client_id', secret_id='secret_id',
        region='region', ssl_cert_generate=True)

    user_data = csp._user_data.decode()
    tmp_crt = csp._ssl_cert_crt
    tmp_key = csp._ssl_cert_key
    with open(tmp_crt, 'rt') as file:
        assert file.read() in user_data
    with open(tmp_key, 'rt') as file:
        assert file.read() in user_data

    csp._instance_id = True
    csp.stop(stop_mode='term')
    assert not os.path.isfile(tmp_crt)
    assert not os.path.isfile(tmp_key)

    # Missing key
    with pytest.raises(HostConfigurationException):
        assert DummyCSP(client_id='client_id', secret_id='secret_id',
                 region='region', ssl_cert_key=str(ssl_key_file))._user_data

    # Missing crt
    with pytest.raises(HostConfigurationException):
        assert DummyCSP(client_id='client_id', secret_id='secret_id',
                 region='region', ssl_cert_crt=str(ssl_crt_file))._user_data
