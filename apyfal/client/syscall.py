# coding=utf-8
"""Accelerator system call client."""

import json as _json
from os import remove as _remove
from os.path import join as _join, exists as _exists
from subprocess import Popen as _Popen, PIPE as _PIPE
from uuid import uuid4 as _uuid

import apyfal.exceptions as _exc
from apyfal.client import AcceleratorClient as _Client
import apyfal.configuration as _cfg


def _call(command, check_file=None, **exc_args):
    """
    Call command in subprocess.

    Args:
        command (str or list or tuple): Command to call.
        check_file (str): Returns file content in exception if exists.
        exc_args: Extra arguments for exception to raise
            if error.

    Raises:
        apyfal.exceptions.ClientRuntimeException:
            Error while calling command.
    """
    try:
        process = _Popen(
            command, stdout=_PIPE, stderr=_PIPE, universal_newlines=True,
            shell=False)
        outputs = list(process.communicate())
        in_error = process.returncode
    except OSError as exception:
        in_error = True
        outputs = [str(exception)]
    if in_error:
        if check_file and _exists(check_file):
            with open(check_file, 'rt') as file:
                outputs.append(file.read())
        raise _exc.ClientRuntimeException(exc='\n'.join(
            [command if isinstance(command, str) else ' '.join(command)] +
            [output for output in outputs if output]), **exc_args)


def _systemctl(command, *services):
    """Start or stop service using systemctl

    Args:
        services (str): service name.
        command (str): "start" or "stop"
    """
    for service in services:
        _call(['sudo', 'systemctl', command, '%s.service' % service],
              gen_msg=('unable_to_named', command, '%s service' % service))


class SysCallClient(_Client):
    """
    Accelerator client.

    Args:
        accelize_client_id (str): Accelize Client ID.
            Client ID is part of the access key generate from
            "https:/accelstore.accelize.com/user/applications".
        accelize_secret_id (str): Accelize Secret ID. Secret ID come with client_id.
        config (str or apyfal.configuration.Configuration or file-like object):
            Can be Configuration instance, apyfal.storage URL, paths, file-like object.
            If not set, will search it in current working directory, in current
            user "home" folder. If none found, will use default configuration values.
    """

    #: Client type
    NAME = 'SysCall'

    def __init__(self, *args, **kwargs):
        _Client.__init__(self, *args, **kwargs)

        self._metering_env = None

        # Need accelerator executable to run
        if not _cfg.accelerator_executable_available():
            raise _exc.HostConfigurationException(
                gen_msg='no_host_found')

    def _start(self, datafile, parameters):
        """
        Client specific start implementation.

        Args:
            datafile (str): Input file.
            parameters (dict): Parameters dict.

        Returns:
            dict: response.
        """
        # Initialize metering
        self._init_metering(parameters)

        # Run and return response
        return self._run_executable(
            mode='0',
            input_file=datafile,
            input_json=str(_uuid()),
            output_json=str(_uuid()),
            parameters=parameters,
        )

    def _process(self, file_in, file_out, parameters):
        """
        Client specific process implementation.

        Args:
            file_in (str): Input file.
            file_out (str): Output file.
            parameters (dict): Parameters dict.

        Returns:
            dict: response dict.
        """
        return self._run_executable(
            mode='1',
            input_file=file_in,
            output_file=file_out,
            input_json=str(_uuid()),
            output_json=str(_uuid()),
            parameters=parameters,

            # Reduces verbosity to minimum by default
            extra_args=['-v4'],
        )

    def _stop(self, info_dict):
        """
        Client specific stop implementation.

        Args:
            info_dict (bool): Returns response dict.

        Returns:
            dict or None: response.
        """
        if not _cfg.accelerator_executable_available():
            # Don't try to stop accelerator if not present
            return

        response = self._run_executable(
            mode='2',
            output_json=str(_uuid()) if info_dict else None
        )

        # Stops services
        # TODO: Better to not stop services ?
        _systemctl('stop', 'meteringclient', 'meteringsession')

        # Gets optional information
        return response

    def _run_executable(
            self, mode, input_file=None, output_file=None, input_json=None,
            output_json=None, parameters=None, extra_args=None):
        """
        Run accelerator executable.

        Args:
            mode (str): Accelerator mode ("0": start, "1": process, "2": stop)
            input_file (str): Input data file path.
            output_file (str): Output data file path.
            input_json (str): Input JSON file path.
            output_json: (str): Output JSON file path.
            parameters (dict): Parameters dict.
            extra_args (list of str): Extra accelerator arguments.

        Returns:
            dict or None: Content of output_json if any.
        """
        # Command base
        command = ['sudo', _cfg.ACCELERATOR_EXECUTABLE, '-m', mode]

        # Adds extra command line arguments
        if extra_args:
            command.extend(extra_args)

        # Input file
        if input_file:
            command += ['-i', input_file]

        # Output file
        if output_file:
            command += ['-o', output_file]

        # Input JSON file
        if input_json and parameters:
            input_json = _join(self._tmp_dir, input_json)
            with open(input_json, 'wt') as json_input_file:
                _json.dump(parameters, json_input_file)
            command += ['-j', input_json]

        # Output JSON file
        if output_json:
            output_json = _join(self._tmp_dir, output_json)
            command += ['-p', output_json]

        # Runs command
        _call(command, check_file=output_json)

        # Cleanup input JSON file
        if input_json:
            _remove(input_json)

        # Gets result from output JSON file
        if output_json:
            with open(output_json, 'rt') as json_output_file:
                response = _json.load(json_output_file)

            # Cleanup output JSON file
            _remove(output_json)
            return response

    def _init_metering(self, parameters):
        """Initialize metering services.

        Args:
            parameters (dict): start parameters.
        """
        new_env = {
            key: parameters['env'].get(key) for key in
            ('AGFI', 'client_id', 'client_secret')}

        # Cached value match with new env: Already configured
        if new_env == self._metering_env:
            return

        # Get current configuration
        cur_env = {key: None for key in new_env}
        if _exists(_cfg.METERING_CREDENTIALS):
            # Get current credentials
            with open(_cfg.METERING_CREDENTIALS, 'rt') as file:
                cur_env.update(_json.load(file))

        if _exists(_cfg.METERING_CLIENT_CONFIG):
            # Get current AGFI configuration
            with open(_cfg.METERING_CLIENT_CONFIG, 'rt') as file:
                for line in file:
                    key, value = line.strip().split('=')
                    if key == 'AFI':
                        cur_env['AGFI'] = value
                        break

        full_env = {
            key: new_env.get(key) or cur_env.get(key)
            for key in new_env}

        # Cached value match with full env: Already configured
        if full_env == self._metering_env:
            return

        # Checks if credentials needs to be updated
        update_credentials = (
            'client_id' in new_env and
            (new_env['client_id'] != cur_env['client_id'] or
             new_env['client_secret'] != cur_env['client_secret']))

        if update_credentials:
            # Update credential in config
            for cred_key, config_key in (('client_id', 'client_id'),
                                         ('client_secret', 'secret_id')):
                self._config['accelize'][config_key] = full_env[cred_key]
                self._configuration_parameters['env'][config_key] = full_env[cred_key]

            # Checks if credentials are valid
            new_env['access_token'] = self._config.access_token

        elif cur_env['client_id'] is None:
            # No credentials
            raise _exc.ClientAuthenticationException(gen_msg='no_credentials')

        # Checks if AGFI needs to be updated
        update_agfi = (
            new_env['AGFI'] and new_env['AGFI'] != cur_env['AGFI'])

        # All is already up to date: caches values
        if not update_agfi or not update_credentials:
            self._metering_env = full_env
            return

        # Stop services
        _systemctl(
            'stop', 'accelerator', 'meteringsession', 'meteringclient')

        # Update
        try:
            # Clear cache
            if _exists(_cfg.METERING_TMP):
                _call(['sudo', 'rm', _cfg.METERING_TMP])

            # Credentials
            if update_credentials:
                _call(['sudo', 'chmod', 'a+wr', _cfg.METERING_CREDENTIALS])
                with open(_cfg.METERING_CREDENTIALS, 'wt') as credential_file:
                    _json.dump({
                        key: full_env[key] for key in ('client_id', 'client_secret')},
                        credential_file)

            # AGFI
            if update_agfi:
                _call(['sudo', 'echo', '"AFI=%s"' % full_env['AGFI'], '>',
                       _cfg.METERING_CLIENT_CONFIG])

        # Restart services
        finally:
            _systemctl(
                'start', 'accelerator', 'meteringclient', 'meteringsession')

        # Cache values
        self._metering_env = full_env
