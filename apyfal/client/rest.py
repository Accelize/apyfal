# coding=utf-8
"""Accelerator REST client.

This client allow remote accelerator control."""
import json as _json
import shutil as _shutil

from requests.exceptions import HTTPError as _HTTPError
from requests_toolbelt.multipart.encoder import (
    MultipartEncoder as _MultipartEncoder)

import apyfal._utilities as _utl
import apyfal.exceptions as _exc
from apyfal.client import AcceleratorClient as _Client


class RESTClient(_Client):
    """
    Remote Accelerator OpenAPI REST client.

    Args:
        accelerator (str): Name of the accelerator to initialize,
            to know the accelerator list please visit
            "https://accelstore.accelize.com".
        accelize_client_id (str): Accelize Client ID.
            Client ID is part of the access key generate from
            "https:/accelstore.accelize.com/user/applications".
        accelize_secret_id (str): Accelize Secret ID. Secret ID come with
            client_id.
        host_ip (str): IP or URL address of the accelerator host.
        config (apyfal.configuration.Configuration, path-like object or file-like object):
            If not set, will search it in current working directory,
            in current user "home" folder. If none found, will use default
            configuration values.
            Path-like object can be path, URL or cloud object URL.
    """

    #: Client type
    NAME = 'REST'

    # Client is remote or not
    REMOTE = True

    # Format required for parameter: 'file' (default) or 'stream'
    _PARAMETER_IO_FORMAT = {
        'file_in': 'stream', 'file_out': 'stream', 'datafile': 'stream'}

    # REST API routes
    _REST_API = {
        'process': '/v1.0/process/',
        'start': '/v1.0/configuration/',
        'stop': '/v1.0/stop/'}

    def __init__(self, accelerator=None, host_ip=None, *args, **kwargs):
        # Initialize client
        _Client.__init__(self, accelerator=accelerator, *args, **kwargs)

        # Initializes HTTP client
        self._configuration_url = None
        self._session = _utl.http_session(max_retries=3)
        self._endpoints = {}

        # Mandatory parameters
        if not accelerator:
            raise _exc.ClientConfigurationException(
                "'accelerator' argument is mandatory.")

        # Pass host URL if already defined.
        if host_ip:
            self.url = host_ip

    @property
    def url(self):
        """
        URL of the accelerator host.

        Returns:
            str: URL
        """
        return self._url

    @url.setter
    def url(self, url):
        # Check URL
        if not url:
            raise _exc.ClientConfigurationException("Host URL is not valid.")

        self._url = url = _utl.format_url(url)

        for route in self._REST_API:
            self._endpoints[route] = url + self._REST_API[route]

        # If possible use the last accelerator configuration (it can still be
        # overwritten later)
        self._use_last_configuration()

    def _is_alive(self):
        """
        Check if accelerator URL exists.

        Raises:
            ClientRuntimeException: If URL not alive
        """
        if self.url is None:
            raise _exc.ClientRuntimeException("No accelerator running")
        if not _utl.check_url(self.url, max_retries=2):
            raise _exc.ClientRuntimeException(
                gen_msg=('unable_reach_url', self._url))

    def _use_last_configuration(self):
        """
        Reload last accelerator configuration.
        """
        # Get last configuration, if any
        response = self._session.get(self.url + self._REST_API['start'])
        try:
            last_config = response.json()['results'][0]
        except (KeyError, IndexError, ValueError):
            return

        # The last configuration URL should be keep in order to not request
        # it to user.
        if last_config['used'] != 0:
            self._configuration_url = last_config['url']

    def start(self, datafile=None, info_dict=False, host_env=None,
              **parameters):
        """
        Configures accelerator.

        Args:
            datafile (path-like object or file-like object): Depending on the
                accelerator, a configuration data file need to be loaded before
                a process can be run.
                Path-like object can be path, URL or cloud object URL.
            info_dict (bool): If True, returns a dict containing information on
                configuration operation.
            parameters (str, path-like object or dict):
                Accelerator configuration specific
                parameters Can also be a full configuration parameters
                dictionary (Or JSON equivalent as str literal or apyfal.storage
                URL to file) Parameters dictionary override default
                configuration values, individuals specific parameters overrides
                parameters dictionary values. Take a look to accelerator
                documentation for more information on possible parameters.
                Path-like object can be path, URL or cloud object URL.

        Returns:
            dict: Optional, only if "info_dict" is True. AcceleratorClient
                response. AcceleratorClient contain output information from
                configuration operation. Take a look accelerator documentation
                for more information.
        """
        # Skips configuration if already configured
        if not (self._configuration_url is None or datafile or parameters or
                host_env):
            return

        # Starts
        return _Client.start(
            self, datafile=datafile, info_dict=info_dict, host_env=host_env,
            **parameters)

    def _start(self, datafile, parameters):
        """
        Client specific start implementation.

        Args:
            datafile (str or file-like object): Input file.
            parameters (dict): Parameters dict.

        Returns:
            dict: response.
        """
        # Post accelerator configuration
        fields = {'parameters': _json.dumps(parameters)}
        if datafile:
            fields['datafile'] = (
                'datafile', datafile, 'application/octet-stream')
        multipart = _MultipartEncoder(fields=fields)

        response = self._session.post(
            self._endpoints['start'], data=multipart, headers={
                'Content-Type': multipart.content_type})

        # Checks response, gets Configuration result
        response_dict = self._raise_for_error(response)
        config_result = response_dict['parametersresult']

        # Checks if configuration was successful
        response_dict = self._raise_for_error(self._session.get(
            self._endpoints['start'] + str(response_dict['id'])))

        # Memorizes configuration
        self._configuration_url = response_dict['url']

        # Returns response
        config_result['url_config'] = self._configuration_url
        config_result['url_instance'] = self.url
        return config_result

    def _process(self, file_in, file_out, parameters):
        """
        Client specific process implementation.

        Args:
            file_in (file-like object): Input file.
            file_out (file-like object): Output file.
            parameters (dict): Parameters dict.

        Returns:
            dict: response dict.
        """
        # Check if configuration was done
        if self._configuration_url is None:
            raise _exc.ClientConfigurationException(
                "AcceleratorClient has not been configured. "
                "Use 'start' function.")

        # Post processing request
        fields = {
            'parameters': _json.dumps(parameters),
            'configuration': self._configuration_url}
        if file_in:
            fields['datafile'] = 'file_in', file_in, 'application/octet-stream'
        multipart = _MultipartEncoder(fields=fields)

        response = self._session.post(
            self._endpoints['process'], data=multipart, headers={
                'Content-Type': multipart.content_type})

        # Check response and append process ID to process URL
        process_url = self._endpoints['process'] + str(
            self._raise_for_error(response)['id'])

        # Get result
        try:
            # Wait processing
            while True:
                response_dict = self._raise_for_error(
                    self._session.get(process_url))
                if response_dict['processed']:
                    break

            # Gets result file
            if file_out:
                response = self._session.get(
                    response_dict['datafileresult'], stream=True)
                _shutil.copyfileobj(response.raw, file_out)

            # Gets result dict
            return response_dict['parametersresult']

        finally:
            # Deletes process result on server
            self._session.delete(process_url)

    def _stop(self, info_dict):
        """
        Client specific stop implementation.

        Args:
            info_dict (bool): Returns response dict.

        Returns:
            dict or None: response.
        """
        if self._stopped:
            # Avoid double call with __exit__ + __del__
            return
        self._stopped = True

        try:
            self._is_alive()
        except _exc.ClientRuntimeException:
            # No AcceleratorClient to stop
            return None

        # Sends stop to server
        response = self._session.get(self.url + self._REST_API['stop'])
        if info_dict:
            return response.json()

    @staticmethod
    def _raise_for_error(response):
        """
        Raises for error and returns response dict.

        Args:
            response (requests.Response): Response

        Returns:
            dict: Response JSON dict

        Raises:
            apyfal.exceptions.ClientRuntimeException: Error.
        """
        # Handles requests HTTP errors
        try:
            response.raise_for_status()
        except _HTTPError as exception:
            raise _exc.ClientRuntimeException(exc=exception)

        # Gets result as dict
        try:
            response_dict = response.json()
        except ValueError:
            raise _exc.ClientRuntimeException(
                "Unable to parse host response", exc=response.text)

        # Checks error flag
        if response_dict.get('inerror', True):
            raise _exc.ClientRuntimeException(
                "Host returned an error", exc=response.text)

        return response_dict
