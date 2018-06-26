# coding=utf-8
"""apyfal.client tests"""
import json
import os

import pytest
import requests


def has_accelize_credential(config):
    """
    Check if Accelize credentials are present in
    configuration file.

    Args:
        config: Configuration file.

    Returns:
        bool: True if credentials founds in file.
    """
    return (config['accelize']['client_id'] and
            config['accelize']['secret_id'])


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
    DummyConfiguration()

    # Test: Use linked configuration file
    config_file = tmpdir.join(dummy_configuration)
    config_file.write(content)
    config = DummyConfiguration(str(config_file))
    assert has_accelize_credential(config)

    # Test: Use file from home
    config_file = os.path.join(
        os.path.expanduser('~'), dummy_configuration)
    with open(config_file, 'wt') as home_file:
        home_file.write(content)

    try:
        config = DummyConfiguration()
        assert has_accelize_credential(config)

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


def accelize_credentials_available():
    """
    Checks in Accelize credentials are available.
    Skips test if not, else, returns configuration.

    Returns:
        apyfal.configuration.Configuration
    """
    from apyfal.configuration import Configuration
    config = Configuration()
    if not has_accelize_credential(config):
        pytest.skip('Accelize Credentials required')
    return config


@pytest.mark.need_accelize
def test_configuration_access_token():
    """Tests Configuration._access_token

    without Accelize server"""
    from apyfal.configuration import Configuration, METERING_SERVER
    import apyfal.exceptions as exc

    # Mocks some variables
    access_token = 'dummy_token'
    client_id = 'dummy_client_id',
    secret_id = 'dummy_secret_id'

    # Mocks requests in utilities

    class Response:
        """Fake requests.Response"""
        status_code = 200
        text = json.dumps({'access_token': access_token})

        @staticmethod
        def raise_for_status():
            """Do nothing"""

    class DummySession(requests.Session):
        """Fake requests.Session"""

        @staticmethod
        def post(url, data, auth, **_):
            """Checks input arguments and returns fake response"""
            # Checks input arguments
            assert METERING_SERVER in url
            assert client_id in auth
            assert secret_id in auth

            # Returns fake response
            return Response()

    # Monkey patch requests in utilities
    requests_session = requests.Session
    requests.Session = DummySession

    # Tests
    try:
        # Test: No credential provided
        config = Configuration()
        try:
            del config._sections['accelize']
        except KeyError:
            pass
        with pytest.raises(exc.ClientAuthenticationException):
            assert config._access_token

        # Test: Everything OK
        config = Configuration()
        config['accelize']  # Creates section if not exists
        config._sections['accelize']['client_id'] = client_id
        config._sections['accelize']['secret_id'] = secret_id
        assert config._access_token == access_token

        # Test: Check dict features
        assert len(config) == len(config._sections)
        for section in config:
            assert section in config._sections
            assert section in config

        config._sections['accelize']['test_value'] = '1,2,3'
        assert config['accelize'].get_literal('test_value') == (1, 2, 3)

        # Test cached value
        del config._sections['accelize']
        assert config._access_token == access_token

        # Test: Authentication failed
        config = Configuration()
        try:
            del config._sections['accelize']
        except KeyError:
            pass
        Response.status_code = 400
        with pytest.raises(exc.ClientAuthenticationException):
            assert config._access_token

    # Restore requests
    finally:
        requests.Session = requests_session


@pytest.mark.need_accelize
def test_configuration_access_token_real():
    """Tests Configuration._access_token

    with Accelize server
    Test parts that needs credentials"""
    # Skip test if Accelize credentials not available
    config = accelize_credentials_available()

    # Import modules
    from apyfal.exceptions import ClientAuthenticationException

    # Test: Valid credentials
    # Assuming Accelize credentials in configuration file are valid, should pass
    try:
        assert config._access_token
    except ClientAuthenticationException as exception:
        if 'invalid_client' in str(exception):
            pytest.xfail("No valid Accelize credential")
        else:
            raise

    # Test: Keep same client_id but use bad secret_id
    config['accelize']['secret_id'] = 'bad_secret_id'
    config._cache = {}
    with pytest.raises(ClientAuthenticationException):
        assert config._access_token


@pytest.mark.need_accelize
def test_configuration_access_token_real_no_cred():
    """Tests AcceleratorClient._access_token

    with Accelize server
    Test parts that don't needs credentials"""
    from apyfal.exceptions import ClientAuthenticationException
    from apyfal.configuration import Configuration

    config = Configuration()
    try:
        del config._sections['accelize']
    except KeyError:
        pass
    config['accelize']['client_id'] = 'bad_client_id'
    config['accelize']['secret_id'] = 'bad_secret_id'

    # Test: Bad client_id
    with pytest.raises(ClientAuthenticationException):
        assert config._access_token


def test_configuration_get_host_requirements():
    """Tests Configuration.get_host_requirements

    without Accelize server"""
    from apyfal.configuration import METERING_SERVER, Configuration
    from apyfal.exceptions import ClientConfigurationException

    # Mocks some variables
    access_token = 'dummy_token'
    host_type = 'dummy_host_type'
    accelerator = 'dummy_accelerator'
    config = {'dummy_config': None}

    # Mock some accelerators parts
    class DummyConfiguration(Configuration):
        """Dummy Configuration"""

        @property
        def _access_token(self):
            """Don't check credential"""
            return access_token

    # Mocks requests in utilities
    class Response:
        """Fake requests.Response"""
        text = json.dumps({host_type: {accelerator: config}})

        @staticmethod
        def raise_for_status():
            """Do nothing"""

    class DummySession(requests.Session):
        """Fake requests.Session"""

        @staticmethod
        def get(url, headers, **_):
            """Checks input arguments and returns fake response"""
            # Checks input arguments
            assert METERING_SERVER in url
            assert access_token in headers['Authorization']

            # Returns fake response
            return Response()

    # Monkey patch requests in utilities
    requests_session = requests.Session
    requests.Session = DummySession

    # Tests
    try:
        # Test: Invalid AcceleratorClient name
        configuration = DummyConfiguration()
        with pytest.raises(ClientConfigurationException):
            configuration.get_host_requirements(
                host_type, 'accelerator_not_exists')

        # Test: Provider not exists
        configuration = DummyConfiguration()
        with pytest.raises(ClientConfigurationException):
            configuration.get_host_requirements(
                'host_not_exists', accelerator)

        # Test: Everything OK
        configuration = DummyConfiguration()
        response = configuration.get_host_requirements(host_type, accelerator)
        config['accelerator'] = accelerator
        assert response == config

    # Restore requests
    finally:
        requests.Session = requests_session


@pytest.mark.need_accelize
def test_configuration_get_requirements_real():
    """Tests Configuration.get_host_requirements

    with Accelize server"""
    # Skip test if Accelize credentials not available
    config = accelize_credentials_available()

    # Import modules
    import apyfal.exceptions as exc

    # Test: Invalid AcceleratorClient name
    with pytest.raises(exc.ClientConfigurationException):
        try:
            config.get_host_requirements('OVH', 'accelerator_not_exists')
        except exc.ClientAuthenticationException:
            pytest.skip("No valid Accelize credential")
            return

    # Test: Provider not exists
    with pytest.raises(exc.ClientConfigurationException):
        config.get_host_requirements('no_exist_host', 'axonerve_hyperfire')

    # Test: Everything OK
    name = 'axonerve_hyperfire'
    response = config.get_host_requirements('OVH', 'axonerve_hyperfire')
    assert response['accelerator'] == name


def dumps_config(config_dict, config_file):
    """Save config_dict in file

    Args:
        config_dict (dict): Configuration file content
        config_file: File handler."""
    content = []
    for section, options in config_dict.items():
        content.append('[%s]' % section)
        for option, value in options.items():
            content.append('%s=%s' % (option, value))
    config_file.write('\n'.join(content))


def test_legacy_backward_compatibility(tmpdir):
    """Test Configuration._legacy_backward_compatibility"""
    from apyfal.configuration import Configuration, create_configuration

    # Temporary configuration file
    config_file = tmpdir.join(
        Configuration.DEFAULT_CONFIG_FILE)
    config_path = str(config_file)

    # Compatibility with acceleratorAPI
    legacy_ssh_key = 'legacy_ssh_key'
    legacy_provider = 'legacy_provider'
    legacy_instance_ip = 'legacy_instance_ip'
    legacy_conf = {
        'csp': {
            'ssh_key': legacy_ssh_key,
            'provider': 'legacy_provider',
            'instance_ip': 'legacy_instance_ip'
        }}
    dumps_config(legacy_conf, config_file)
    config = create_configuration(config_path)
    assert config['host']['key_pair'] == legacy_ssh_key
    assert config['host']['host_type'] == legacy_provider
    assert config['host']['host_ip'] == legacy_instance_ip

    # Check not overwrite existing with legacy
    key_pair = 'key_pair'
    legacy_conf = {
        'csp': {'ssh_key': legacy_ssh_key},
        'host': {'key_pair': key_pair}
    }
    dumps_config(legacy_conf, config_file)
    config = create_configuration(config_path)
    assert config['host']['key_pair'] == key_pair


def test_subsections(tmpdir):
    """Test Configuration subsection"""
    from apyfal.configuration import Configuration, create_configuration

    # Temporary configuration file
    config_file = tmpdir.join(
        Configuration.DEFAULT_CONFIG_FILE)
    config_path = str(config_file)

    # Compatibility with acceleratorAPI
    conf = {
        'section': {
            'key1': '1',
            'key2': '2',
        },
        'section.subsection': {
            'key1': '1.1',
            'key3': '1.3'
        },
        'section.subsection.subsubsection': {
            'key1': '1.1.1',
        }
    }
    dumps_config(conf, config_file)
    config = create_configuration(config_path)

    # Test: reading
    assert config['section']['key1'] == '1'
    assert config['section']['key2'] == '2'
    assert config['section']['key3'] is None

    assert config['section.subsection']['key1'] == '1.1'
    assert config['section.subsection']['key2'] == '2'
    assert config['section.subsection']['key3'] == '1.3'

    assert config['section.subsection.subsubsection'
                  ]['key1'] == '1.1.1'

    assert config['section'].get_literal('key1') == 1
    assert config['section.subsection.subsubsection'
                  ].get_literal('key1') == '1.1.1'

    # Test: writing
    config['section']['key1'] = None
    assert config['section']['key1'] == '1'

    config['section']['key1'] = '0'
    assert config['section']['key1'] == '0'

    assert config['section'].set('key1', '1') == '1'
    assert config['section'].set('key1', None) == '1'

    # Test: Presence
    assert 'section' in config
    assert 'section_not_exists' not in config

    assert 'key1' in config['section']
    assert 'key10' not in config['section']
