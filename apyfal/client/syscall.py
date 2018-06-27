# coding=utf-8
"""Accelerator system call client."""

import json as _json
from subprocess import Popen as _Popen, PIPE as _PIPE
from uuid import uuid4 as _uuid

import apyfal.exceptions as _exc
from apyfal.client import AcceleratorClient as _Client


def _call(command, **exc_args):
    """
    Call command.

    Args:
        command (str or list or tuple): Command to call.
        exc_args: Extra arguments for exception to raise
            if error.

    Raises:
        apyfal.exceptions.ClientRuntimeException:
            Error while calling command.
    """
    process = _Popen(
        command, stdout=_PIPE, stderr=_PIPE, universal_newlines=True)
    outputs = process.communicate()
    if process.returncode:
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
        accelerator (str): Name of the accelerator you want to initialize,
            to know the accelerator list please visit "https://accelstore.accelize.com".
        accelize_client_id (str): Accelize Client ID.
            Client ID is part of the access key you can generate on
            "https:/accelstore.accelize.com/user/applications".
        accelize_secret_id (str): Accelize Secret ID. Secret ID come with client_id.
        host_ip (str): IP or URL address of the accelerator host.
        config (str or apyfal.configuration.Configuration or file-like object):
            Can be Configuration instance, apyfal.storage URL, paths, file-like object.
            If not set, will search it in current working directory, in current
            user "home" folder. If none found, will use default configuration values.
    """
    ACCELERATOR_PATH = '/opt/accelize/accelerator/accelerator'

    def start(self, datafile=None, info_dict=False, host_env=None, **parameters):
        """
        Configures accelerator.

        Args:
            datafile (str): Depending on the accelerator,
                a configuration need to be loaded before a process can be run.
                In such case please define the path of the configuration file.
            info_dict (bool): If True, returns a dict containing information on
                configuration operation.
            parameters (str or dict): Accelerator configuration specific parameters
                Can also be a full configuration parameters dictionary
                (Or JSON equivalent as str literal or path to file)
                Parameters dictionary override default configuration values,
                individuals specific parameters overrides parameters dictionary values.
                Take a look to accelerator documentation for more information on possible parameters.

        Returns:
            dict: Optional, only if "info_dict" is True. AcceleratorClient response.
                AcceleratorClient contain output information from  configuration operation.
                Take a look accelerator documentation for more information.
        """
        # Command base
        command = ['sudo', self.ACCELERATOR_PATH, '-m', '0']

        # Add datafile if any
        if datafile:
            command += ['-i', datafile]

        # Checks parameters
        # TODO: common parameter handling with other client
        parameters = self._get_parameters(parameters, self._configuration_parameters)
        parameters.update({
            "env": {"client_id": self._client_id, "client_secret": self._secret_id}})
        parameters['env'].update(host_env or dict())

        # Create input JSON file if needed
        # TODO: json path
        if parameters:
            json_input = 'input.json'
            with open(json_input, 'wb') as json_input_file:
                _json.dump(parameters, json_input_file)
            command += ['-j', json_input]

        # Select path to output JSON file
        if info_dict:
            # TODO: json path
            json_output = 'output.json'
            command += ['-p', json_output]

        # Initialize metering
        self._init_metering(parameters)

        # Run command
        _call(command)

        # Get optional information
        if info_dict:
            with open(json_output, 'rb') as json_output_file:
                return _json.load(json_output_file)

    def process(self, file_in=None, file_out=None, info_dict=False, **parameters):
        """
        Processes using OpenApi REST API.

        Args:
            file_in (str): Path to the file you want to process.
            file_out (str): Path where you want the processed file will be stored.
            info_dict (bool): If True, returns a dict containing information on
                process operation.
            parameters (str or dict): Accelerator process specific parameters
                Can also be a full process parameters dictionary
                (Or JSON equivalent as str literal or path to file)
                Parameters dictionary override default configuration values,
                individuals specific parameters overrides parameters dictionary values.
                Take a look to accelerator documentation for more information on possible parameters.

        Returns:
            dict: Result from process operation, depending used accelerator.
            dict: Optional, only if "info_dict" is True. AcceleratorClient response.
                AcceleratorClient contain output information from  process operation.
                Take a look accelerator documentation for more information.
        """
        # Command base
        command = ['sudo', self.ACCELERATOR_PATH, '-v4', '-m', '1']

        # Add file_in if any
        if file_in:
            command += ['-i', file_in]

        # Configure processing
        parameters = self._get_parameters(parameters, self._process_parameters)

        # Create input JSON file if needed
        # TODO: json path
        if parameters:
            json_input = 'input.json'
            with open(json_input, 'wb') as json_input_file:
                _json.dump(parameters, json_input_file)
            command += ['-j', json_input]

        # Select path to output JSON file
        json_output = 'output.json'
        command += ['-p', json_output]

        # Add file_out if any
        if file_out:
            command += ['-o', file_out]

        # Run command
        _call(command)

        # Get result from response and returns
        with open(json_output, 'rb') as json_output_file:
            process_response = _json.load(json_output_file)
        try:
            result = process_response['app'].pop('specific')
        except KeyError:
            result = dict()

        if info_dict:
            # Returns with optional response
            return result, process_response
        return result

    def stop(self, info_dict=False):
        """
        Stop accelerator.

        Args:
            info_dict (bool): If True, returns a dict containing information on
                stop operation.

        Returns:
            dict: Optional, only if "info_dict" is True. AcceleratorClient response.
                AcceleratorClient contain output information from  stop operation.
                Take a look to accelerator documentation for more information.
        """
        # Command base
        command = ['sudo', self.ACCELERATOR_PATH, '-m', '2']

        # Select path to output JSON file
        if info_dict:
            # TODO: json path
            json_output = 'output.json'
            command += ['-p', json_output]

        # Run command
        _call(command)

        # Stop services
        # TODO: Better to not stop services ?
        _systemctl('stop', 'meteringclient', 'meteringsession')

        # Get optional information
        if info_dict:
            with open(json_output, 'rb') as json_output_file:
                return _json.load(json_output_file)

    @staticmethod
    def _init_metering(parameters):
        """Initialize metering services.

        Args:
            parameters (dict): start parameters.
        """
        # Stop services
        _systemctl(
            'stop', 'accelerator', 'meteringsession', 'meteringclient')

        # Clear cache
        _call(['sudo', 'rm', '/tmp/meteringServer'])

        # Legacy metering: Generate metering configuration file
        first_call = True
        for key, value in (('USER_ID', parameters['env'].get('client_id')),
                           ('SESSION_ID', _uuid()),
                           ('AFI', parameters['env'].get('AGFI'))):
            if not value:
                continue
            _call(['sudo', 'echo', '"%s=%s"' % (key, value),
                   '>' if first_call else '>>',
                   '/etc/sysconfig/meteringclient'])
            first_call = False

        # New metering: Generate metering configuration file
        if 'client_id' in parameters['env']:
            credentials = '/etc/accelize/credentials.json'
            # Set right
            _call(['sudo', 'chmod', 'a+wr', credentials])
            with open(credentials, 'wb') as credential_file:
                _json.dump(
                    {key: parameters['env'][key]
                     for key in ('client_id', 'client_secret')},
                    credential_file)

        # Restart services
        _systemctl(
            'start', 'accelerator', 'meteringclient', 'meteringsession')
