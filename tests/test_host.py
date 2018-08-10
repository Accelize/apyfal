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
    try:
        del config._sections['host']
    except KeyError:
        pass
    # Test: Not existing host module
    with pytest.raises(HostConfigurationException):
        Host(host_type="no_existing_csp")

    # Test: Instantiation of without specify host_type
    host = Host(config=config)
    assert host.__class__ is Host

    # Test: repr
    assert repr(host) == str(host)

    # Test: Passing host_ip
    url = 'http://127.0.0.1'
    host = Host(config=config, host_ip=url)
    host.start()
    assert host.url == url

    # Test: Passing nothing
    host = Host(config=config)
    with pytest.raises(HostConfigurationException):
        host.start()

    # Test: iter_hosts
    assert list(host.iter_hosts()) == []

