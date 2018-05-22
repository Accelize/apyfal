# coding=utf-8
"""acceleratorAPI.csp tests"""
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


def run_full_real_test_sequence(config):
    """Run common real tests for all CSP.

    Args:
        config (acceleratorAPI.configuration.Configuration): configuration
    """
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
