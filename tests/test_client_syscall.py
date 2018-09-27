# coding=utf-8
"""apyfal.client.syscall tests"""

from contextlib import contextmanager
from copy import deepcopy
import json
import os
from threading import Lock

try:
    # Python 2
    from StringIO import StringIO
except ImportError:
    # Python 3
    from io import StringIO

import pytest


def test_call(tmpdir):
    """Tests _call"""
    import subprocess
    import apyfal.client.syscall as syscall
    from apyfal.exceptions import ClientRuntimeException

    # Mock Popen

    dummy_stdout = 'dummy_stdout'
    dummy_stderr = 'dummy_stderr'
    dummy_file_content = 'dummy_file'.encode()
    dummy_file = tmpdir.join('file')
    dummy_file.write(dummy_file_content)
    dummy_args = ['arg0', 'arg1']
    dummy_oserror = 'dummy_oserror'
    raises_oserror = False

    class DummyPopen:

        returncode = 0

        @staticmethod
        def __init__(args, *_, **__):
            """Check parameters"""
            assert args == dummy_args
            if raises_oserror:
                raise OSError(dummy_oserror)

        @staticmethod
        def communicate():
            """Returns fake result"""
            return dummy_stdout, dummy_stderr

    subprocess_popen = subprocess.Popen
    subprocess.Popen = DummyPopen
    syscall._Popen = DummyPopen

    # Tests
    try:
        # Everything OK
        syscall._call(dummy_args)

        # Bad Error code
        DummyPopen.returncode = 1
        with pytest.raises(ClientRuntimeException) as exception:
            syscall._call(dummy_args, check_file=str(dummy_file))
            assert ' '.join(dummy_args) in str(exception)
            assert dummy_stdout in str(exception)
            assert dummy_stderr in str(exception)
            assert dummy_file_content in str(exception)

        # Raise OSError
        raises_oserror = True
        with pytest.raises(ClientRuntimeException) as exception:
            syscall._call(dummy_args)
            assert ' '.join(dummy_args) in str(exception)
            assert dummy_oserror in str(exception)

    # Restore Popen
    finally:
        subprocess.Popen = subprocess_popen
        syscall._Popen = subprocess_popen


def test_systemctl():
    """Tests _systemctl"""
    import apyfal.client.syscall as syscall

    dummy_command = 'start'
    services = ['service1', 'service2']

    # Mock _call

    def dummy_call(command, *_, **__):
        """Check arguments"""
        assert dummy_command in command
        command = ' '.join(command)
        for service in services:
            if service in command:
                return
        pytest.fail('Service not called')

    syscall_call = syscall._call
    syscall._call = dummy_call

    # Tests
    try:
        syscall._systemctl(dummy_command, *services)

    # Restore _call
    finally:
        syscall._call = syscall_call


def test_syscall_client_init():
    """Tests SysCallClient.__init__"""
    from apyfal.client.syscall import SysCallClient
    from apyfal import Accelerator
    import apyfal.configuration as cfg
    import apyfal.exceptions as exc

    # Test: accelerator_executable_available, checks return type
    assert type(cfg.accelerator_executable_available()) is bool

    # Mocks some functions
    accelerator_available = True

    class DummySysCallClient(SysCallClient):
        """Dummy SysCallClient"""

        @staticmethod
        def _stop(*_, **__):
            """Do Nothing to skip object deletion"""

    def dummy_accelerator_executable_available():
        """Return fake result"""
        return accelerator_available

    cfg_accelerator_executable_available = cfg.accelerator_executable_available
    cfg.accelerator_executable_available = (
        dummy_accelerator_executable_available)

    # Tests
    try:
        # Accelerator not available
        DummySysCallClient()

        # Default for Accelerator if no host specified
        config = cfg.Configuration()
        try:
            del config._sections['host']
        except KeyError:
            pass
        client = Accelerator(config=config).client
        client._stop = DummySysCallClient._stop  # Disable __del__
        assert isinstance(client, SysCallClient)

        # Accelerator not available
        accelerator_available = False
        with pytest.raises(exc.HostConfigurationException):
            SysCallClient()

    # Restores functions
    finally:
        cfg.accelerator_executable_available = (
            cfg_accelerator_executable_available)


def test_syscall_client_run_executable():
    """Tests SysCallClient._run_executable"""
    import apyfal.client.syscall as syscall
    from apyfal.client.syscall import SysCallClient
    import apyfal.configuration as cfg

    exec_arg = 'sudo %s' % cfg.ACCELERATOR_EXECUTABLE
    expected_args = []
    dummy_file = 'file'
    dummy_tmp = 'tmp_dir'
    expected_path = os.path.join(dummy_tmp, dummy_file)
    dummy_params = {'test': 'dummy', 'app': {'arg0': 0}}

    # Mocks some functions
    def dummy_call(command, *_, **__):
        """Check arguments"""
        command = ' '.join(command)
        for arg in expected_args:
            assert arg in command

    def dummy_remove(*_, **__):
        """Do nothing"""

    @contextmanager
    def dummy_open(file, mode, **__):
        """Check arguments and simulate file"""
        assert file == expected_path

        # Simulate file
        stream = StringIO()

        if 'r' in mode:
            json.dump(dummy_params, stream)
            stream.seek(0)

        yield stream

        if 'w' in mode:
            stream.seek(0)
            assert json.load(stream) == dummy_params

    class DummyClient(SysCallClient):

        def __init__(self, *_, **__):
            self._cache = {'tmp_dir': dummy_tmp}
            self._stopped = False
            self._accelerator_lock = Lock()

    syscall_call = syscall._call
    syscall._call = dummy_call
    syscall._remove = dummy_remove
    syscall.open = dummy_open

    # Tests
    try:

        client = DummyClient()

        # Mode
        expected_args = [exec_arg, '-m 3']
        client._run_executable(mode='3')

        # Input file
        expected_args = ['-i %s' % dummy_file]
        client._run_executable(mode='1', input_file=dummy_file)

        # Output file
        expected_args = ['-o %s' % dummy_file]
        client._run_executable(mode='1', output_file=dummy_file)

        # JSON input
        expected_args = ['-j %s' % expected_path]
        client._run_executable(
            mode='1', input_json=dummy_file, parameters=dummy_params)

        # JSON output
        expected_args = ['-p %s' % expected_path]
        assert client._run_executable(
            mode='1', output_json=dummy_file) == dummy_params

        # Extra args
        expected_args = ['arg0', 'arg1']
        client._run_executable(mode='1', extra_args=expected_args)

    # Restores functions
    finally:
        delattr(syscall, 'open')
        syscall._call = syscall_call
        syscall._remove = os.remove


def test_syscall_init_metering(tmpdir):
    """Tests SysCallClient._init_metering"""
    import apyfal.client.syscall as syscall
    from apyfal.client.syscall import SysCallClient
    import apyfal.configuration as cfg
    from apyfal.exceptions import ClientAuthenticationException

    # Mocks some values
    host_type = 'host'
    accelerator = 'accelerator'
    region = 'region'
    client_id = 'dummy_client_id'
    client_secret = 'dummy_client_secret'
    fpga_image = 'dummy_FPGA'
    checks_client_id = False
    default_config = dict()

    # Mocks some functions
    def dummy_call(*_, **__):
        """Do nothing"""

    class DummyConfiguration(cfg.Configuration):
        """Dummy configuration"""

        @property
        def access_token(self):
            """Return fake result"""
            if checks_client_id:
                assert self['accelize']['client_id']
                assert self['accelize']['secret_id']
            return 'dummy_token'

        def get_host_configurations(self):
            """Return fake result"""
            return default_config

    class DummyClient(SysCallClient):
        """Dummy client"""

        def __init__(self, *_, **__):
            self._host_type = host_type
            self._name = accelerator
            self._region = region
            self._metering_env = None
            self._config = DummyConfiguration()
            self._configuration_parameters = {'env': {}}

        def __del__(self):
            """Do nothing"""

    client = DummyClient()

    cfg_metering_credentials = cfg.METERING_CREDENTIALS
    metering_credentials = tmpdir.join('credentials')
    cfg.METERING_CREDENTIALS = str(metering_credentials)

    cfg_metering_client_config = cfg.METERING_CLIENT_CONFIG
    metering_client_config = tmpdir.join('client_config')
    cfg.METERING_CLIENT_CONFIG = str(metering_client_config)

    cfg_metering_tmp = cfg.METERING_TMP
    metering_tmp = tmpdir.join('tmp')
    metering_tmp.ensure()
    cfg.METERING_TMP = str(metering_tmp)

    syscall_call = syscall._call
    syscall._call = dummy_call

    try:
        # Already configured and cached
        client._metering_env = {
            'client_id': client_id,
            'client_secret': client_secret}
        client._init_metering({
            'client_id': client_id,
            'client_secret': client_secret})
        assert not metering_client_config.check()
        assert not metering_credentials.check()

        # Already configured after config file verification
        metering_client_config.write('fpgaimage=%s' % fpga_image)
        client._metering_env = {
            'client_id': client_id,
            'client_secret': client_secret,
            'fpgaimage': fpga_image}
        client._init_metering({
            'client_id': client_id,
            'client_secret': client_secret})
        assert not metering_credentials.check()

        # Not configured and no credentials
        client._metering_env = None
        with pytest.raises(ClientAuthenticationException):
            client._init_metering({})

        # Already configured in files
        client._metering_env = None
        metering_credentials.write(json.dumps({
            'client_id': client_id,
            'client_secret': client_secret}))
        client._init_metering({})
        assert client._metering_env == {
            'client_id': client_id,
            'client_secret': client_secret,
            'fpgaimage': fpga_image}

        # Needs reconfiguration
        new_client_id = 'new_client_id'
        new_fpga_image = 'new_fpga_image'
        client._metering_env = None
        client._init_metering({
            'client_id': new_client_id,
            'fpgaimage': new_fpga_image})
        assert client._metering_env == {
            'client_id': new_client_id,
            'client_secret': client_secret,
            'fpgaimage': new_fpga_image}
        assert json.loads(metering_credentials.read()) == {
            'client_id': new_client_id,
            'client_secret': client_secret}

        # Apyfal 1.0.0 compatibility
        metering_client_config.remove()
        client._metering_env = None
        client._init_metering({'AGFI': fpga_image}, reload=True)
        assert client._metering_env == {
            'fpgaimage': fpga_image, 'AGFI': fpga_image,
            'client_id': new_client_id,
            'client_secret': 'dummy_client_secret'}

        metering_client_config.remove()
        client._metering_env = None
        client._init_metering({'arg': 'arg'}, reload=True)
        assert client._metering_env == {
            'client_id': new_client_id,
            'client_secret': 'dummy_client_secret',
            'arg': 'arg'}

        # Host configuration on non Apyfal started host
        metering_client_config.remove()
        client = DummyClient()
        default_config = {
            host_type: {accelerator: {region: {'fpga_image': fpga_image}}}}
        try:
            del client._config._sections['accelize']
        except KeyError:
            pass
        checks_client_id = True
        client._init_metering(dict())
        assert metering_client_config.check()
        assert fpga_image in metering_client_config.read()

    # Restore
    finally:
        syscall._call = syscall_call
        cfg.METERING_CREDENTIALS = cfg_metering_credentials
        cfg.METERING_CLIENT_CONFIG = cfg_metering_client_config
        cfg.METERING_TMP = cfg_metering_tmp


def test_syscall_client_start_process_stop():
    """Tests SysCallClient._start, _process, _stop"""
    import apyfal.client.syscall as syscall
    import apyfal.configuration as cfg
    from apyfal.exceptions import ClientConfigurationException

    # Mock some client methods
    dummy_file_in = 'file_in'
    dummy_file_out = 'file_out'
    dummy_parameters = {'params': 'params', 'env': {}, 'app': {}}
    dummy_response = {'response': 'response'}
    expected_args = {}

    class DummyClient(syscall.SysCallClient):

        def __init__(self, *_, **__):
            """Do nothing"""
            self._cache = {}
            self._accelerator_lock = Lock()

        def __del__(self):
            """Do nothing"""

        @staticmethod
        def _init_metering(*_, **__):
            """Do nothing"""

        @classmethod
        def _run_executable(cls, mode, **kwargs):
            """Check parameters and returns fake response"""

            # Checks parameters
            kwargs['mode'] = mode
            for key, value in kwargs.items():
                expected = expected_args.get(key)
                if expected == str:
                    assert isinstance(value, str)
                else:
                    assert expected == value

            # Returns response
            if kwargs.get('output_json'):
                return dummy_response

    def dummy_function(*_, **__):
        """Do nothing"""
        return True

    syscall_systemctl = syscall._systemctl
    syscall._systemctl = dummy_function
    cfg_accelerator_executable = cfg.ACCELERATOR_EXECUTABLE
    cfg.ACCELERATOR_EXECUTABLE = __file__

    # Tests:
    try:
        client = DummyClient()

        # Start
        start_parameters = deepcopy(dummy_parameters)
        excepted_parameters = start_parameters.copy()
        del excepted_parameters['env']
        expected_args = dict(
            mode='0', input_file=dummy_file_in, input_json=str,
            output_json=str, parameters=excepted_parameters, extra_args=['-v4'])
        assert client._start(dummy_file_in, start_parameters) == dummy_response

        # Start with version checks
        start_parameters['env']['apyfal_version'] = '0.0.0'
        with pytest.raises(ClientConfigurationException):
            client._start(dummy_file_in, start_parameters)

        start_parameters['env']['apyfal_version'] = '9.9.9'
        assert client._start(dummy_file_in, start_parameters) == dummy_response

        # Process
        expected_args = dict(
            mode='1', input_file=dummy_file_in, output_file=dummy_file_out,
            input_json=str, output_json=str,
            parameters=dummy_parameters, extra_args=['-v4'])
        assert client._process(dummy_file_in, dummy_file_out,
                               dummy_parameters) == dummy_response

        # Stop
        expected_args = dict(mode='2', output_json=str)
        assert client._stop(True) == dummy_response

        expected_args = dict(mode='2', output_json=None)
        assert client._stop(False) is None

    # Restore function
    finally:
        syscall._systemctl = syscall_systemctl
        cfg.ACCELERATOR_EXECUTABLE = cfg_accelerator_executable
