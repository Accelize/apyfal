# coding=utf-8
"""apyfal.client tests"""
import os


def test_configuration(tmpdir):
    """Tests Configuration"""
    from apyfal.configuration import Configuration

    # Mocks configuration
    dummy_configuration = 'dummy_configuration.conf'
    content = ("[accelize]\n"
               "client_id = client\n"
               "secret_id = secret\n")

    class DummyConfiguration(Configuration):
        """Dummy configuration"""
        DEFAULT_CONFIG_FILE = dummy_configuration

    # Test: No configuration file
    config = DummyConfiguration()

    # Test: has_* methods
    assert not config.has_section('accelize')
    assert not config.has_accelize_credential()
    assert not config.has_section('csp')
    assert not config.has_csp_credential()

    # Test: get_default
    assert config.get_default('accelize', 'dummy') is None
    assert config.get_default('accelize', 'dummy', overwrite='1') == '1'
    assert config.get_default('accelize', 'dummy', default='1') == '1'

    config.add_section('accelize')
    config.set('accelize', 'dummy', '2')
    assert config.get_default('accelize', 'dummy') == '2'
    assert config.get_default('accelize', 'dummy', is_literal=True) == 2
    assert config.get_default('accelize', 'dummy', overwrite='1') == '1'
    assert config.get_default('accelize', 'dummy', default='1') == '2'

    config.set('accelize', 'dummy', '')
    assert config.get_default('accelize', 'dummy') is None
    assert config.get_default('accelize', 'dummy', default='2') == '2'

    # Test: Use linked configuration file
    config_file = tmpdir.join(dummy_configuration)
    config_file.write(content)
    config = DummyConfiguration(str(config_file))
    assert config.has_accelize_credential()

    # Test: Use file from home
    config_file = os.path.join(
        os.path.expanduser('~'), dummy_configuration)
    with open(config_file, 'wt') as home_file:
        home_file.write(content)

    try:
        config = DummyConfiguration()
        assert config.has_accelize_credential()

    finally:
        # Remove file from home
        os.remove(config_file)


def test_create_configuration():
    """Tests create_configuration"""
    from apyfal.configuration import (
        create_configuration, Configuration)

    # Test: Create configuration
    config = create_configuration(None)
    assert isinstance(config, Configuration)

    # Test: Returns entry parameter if Configuration
    assert create_configuration(config) is config
