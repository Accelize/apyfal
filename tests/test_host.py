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

    # Test: iter_hosts empty default
    assert list(host._iter_hosts()) == []

    # Test: iter_hosts with proper _iter_host
    def _iter_hosts():
        """dummy iter_host"""
        for index in range(2):
            yield dict(
                public_ip='127.0.0.1',
                host_name='prefix_accelize_pytest%d_000000000000' % index)

    host._iter_hosts = _iter_hosts
    assert list(host.iter_hosts()) == [{
        'public_ip': '127.0.0.1',
        'host_name': 'prefix_accelize_pytest%d_000000000000' % index,
        'accelerator': 'pytest%d' % index,
        'url': 'http://127.0.0.1',
        'host_type': host.host_type,
        '_repr': ("<apyfal.host.Host name='prefix_accelize_"
                  "pytest%d_000000000000'>") % index} for index in range(2)]

    # Test: iter_hosts host_name_prefix
    prefix = 'prefix'
    host = Host(config=config, host_name_prefix=prefix)
    assert host._host_name_prefix == prefix
    assert host._host_name_match is None

    list(host.iter_hosts(host_name_prefix=True))
    assert host._host_name_match is not None
    assert not host._is_accelerator_host('accelize_pytest_000000000000')
    assert not host._is_accelerator_host('other_accelize_pytest_000000000000')
    assert host._is_accelerator_host('prefix_accelize_pytest_000000000000')

    list(host.iter_hosts(host_name_prefix=False))
    assert host._is_accelerator_host('accelize_pytest_000000000000')
    assert host._is_accelerator_host('other_accelize_pytest_000000000000')
    assert host._is_accelerator_host('prefix_accelize_pytest_000000000000')

    list(host.iter_hosts(host_name_prefix='other'))
    assert not host._is_accelerator_host('accelize_pytest_000000000000')
    assert host._is_accelerator_host('other_accelize_pytest_000000000000')
    assert not host._is_accelerator_host('prefix_accelize_pytest_000000000000')

    # Test: not instance names
    list(host.iter_hosts(host_name_prefix=False))
    assert not host._is_accelerator_host('pytest_000000000000')
    assert not host._is_accelerator_host('accelize_000000000000')
    assert not host._is_accelerator_host('accelize_prefix')
    assert not host._is_accelerator_host('accelize_prefix_000')
