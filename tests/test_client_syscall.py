# coding=utf-8
"""apyfal.client.syscall tests"""

from contextlib import contextmanager
import json
import os

try:
    # Python 2
    from StringIO import StringIO
except ImportError:
    # Python 3
    from io import StringIO

import pytest


def test_call():
    """Tests _call"""
    import subprocess
    import apyfal.client.syscall as syscall
    from apyfal.exceptions import ClientRuntimeException

    # Mock Popen

    dummy_stdout = 'dummy_stdout'
    dummy_stderr = 'dummy_stderr'
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
            syscall._call(dummy_args)
            assert ' '.join(dummy_args) in str(exception)
            assert dummy_stdout in str(exception)
            assert dummy_stderr in str(exception)

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

    cfg_accelerator_executable_available = (
        cfg.accelerator_executable_available)
    cfg.accelerator_executable_available = (
        dummy_accelerator_executable_available)

    # Tests
    try:
        # Accelerator not available
        DummySysCallClient('accelerator')

        # Default for Accelerator if no host specified
        config = cfg.Configuration()
        try:
            del config._sections['host']
        except KeyError:
            pass
        client = Accelerator('accelerator', config=config).client
        client._stop = DummySysCallClient._stop  # Disable __del__
        assert isinstance(client, SysCallClient)

        # Accelerator not available
        accelerator_available = False
        with pytest.raises(exc.HostConfigurationException):
            SysCallClient('accelerator')

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
    dummy_params = {
        'test': 'dummy'
    }

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
            self._tmp_dir = dummy_tmp

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

        # Run _init_metering
        expected_args = []
        expected_path = cfg.METERING_CREDENTIALS
        dummy_params = {'client_id': 'dummy_client_id',
                        'client_secret': 'dummy_client_secret'}
        client._init_metering({'env': dummy_params})

    # Restores functions
    finally:
        delattr(syscall, 'open')
        syscall._call = syscall_call
        syscall._remove = os.remove


def test_syscall_client_start_process_stop():
    """Tests SysCallClient._start, _process, _stop"""
    import apyfal.client.syscall as syscall
    import apyfal.configuration as cfg

    # Mock some client methods
    dummy_file_in = 'file_in'
    dummy_file_out = 'file_out'
    dummy_parameters = {'params': 'params'}
    dummy_response = {'response': 'response'}
    expected_args = {}

    class DummyClient(syscall.SysCallClient):

        def __init__(self, *_, **__):
            """Do nothing"""
            self._tmp_dir = None

        def __del__(self):
            """Do nothing"""

        @staticmethod
        def _init_metering(*_):
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
        expected_args = dict(
            mode='0', input_file=dummy_file_in, input_json=str,
            output_json=str, parameters=dummy_parameters)
        assert client._start(dummy_file_in, dummy_parameters) == dummy_response

        # Process
        expected_args = dict(
            mode='1', input_file=dummy_file_in,  output_file=dummy_file_out,
            input_json=str, output_json=str,
            parameters=dummy_parameters, extra_args=['-v4'])
        assert client._process(dummy_file_in, dummy_file_out, dummy_parameters) == dummy_response

        # Stop
        expected_args = dict(mode='2', output_json=str)
        assert client._stop(True) == dummy_response

        expected_args = dict(mode='2', output_json=None)
        assert client._stop(False) is None

    # Restore function
    finally:
        syscall._systemctl = syscall_systemctl
        cfg.ACCELERATOR_EXECUTABLE = cfg_accelerator_executable
