# coding=utf-8
"""apyfal.host tests"""
import pytest


def test_host_init():
    """Tests Host.__new__ and Host.__init__"""
    from apyfal.configuration import Configuration
    from apyfal.host import Host
    from apyfal.exceptions import HostConfigurationException

    # Mock arguments and configuration
    # Note that host_type is not specified here
    config = Configuration()
    config.remove_section('host')

    # Test: Not existing host module
    with pytest.raises(HostConfigurationException):
        Host(host_type="no_existing_csp")

    # Test: Instantiation of without specify host_type
    assert Host(config=config).__class__ is Host

    # Test: Passing host_ip
    url = 'http://127.0.0.1'
    host = Host(config=config, host_ip=url)
    assert host.url == url
