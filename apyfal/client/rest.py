# coding=utf-8
"""Accelerator REST client.

This client allows remote accelerator control."""
import json as _json
import os.path as _os_path
import shutil as _shutil
from uuid import uuid4 as _uuid

from requests.exceptions import HTTPError as _HTTPError
from requests_toolbelt.multipart.encoder import (
    MultipartEncoder as _MultipartEncoder)

import apyfal._utilities as _utl
import apyfal.exceptions as _exc
from apyfal.client import AcceleratorClient as _Client
from apyfal.storage import copy as _srg_copy


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
        ssl_cert_crt (path-like object or file-like object):
            Public ".crt" key file of the SSL ssl_cert_key used by host to
            provides HTTPS. If provided, the ssl_cert_key is verified on each
            request.
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

    # REST API routes
    _REST_API = {
        'process': '/v1.0/process/',
        'start': '/v1.0/configuration/',
        'stop': '/v1.0/stop/'}

    # Number of retries for a request
    _REQUEST_RETRIES = 3

    def __init__(self, accelerator=None, host_ip=None, ssl_cert_crt=None,
                 *args, **kwargs):
        # Initialize client
        _Client.__init__(self, accelerator=accelerator, *args, **kwargs)

        # Initializes HTTP client
        self._ssl_cert_crt = ssl_cert_crt
        self._endpoints = {}

        # Mandatory parameters
        if not accelerator:
            raise _exc.ClientConfigurationException(
                "'accelerator' argument is mandatory.")

        # Pass host URL if already defined.
        if host_ip:
            self.url = host_ip

    @property
    @_utl.memoizedmethod
    def _session(self):
        """
        Requests session

        Returns:
            requests.sessions.Session: Session
        """
        session_kwargs = dict(max_retries=self._REQUEST_RETRIES)

        # Handles SSL certificate
        if self._ssl_cert_crt:
            # Copies certificate locally if not reachable by local path
            if (hasattr(self._ssl_cert_crt, 'read') or
                    not _os_path.exists(self._ssl_cert_crt)):
                ssl_cert_crt = _os_path.join(self._tmp_dir, str(_uuid()))
                _srg_copy(self._ssl_cert_crt, ssl_cert_crt)
                self._ssl_cert_crt = ssl_cert_crt

            session_kwargs['verify'] = self._ssl_cert_crt

            # Disables hostname verification if wildcard (*) certificate
            from apyfal._certificates import \
                get_host_names_from_certificate

            with open(self._ssl_cert_crt, 'rb') as crt_file:
                host_names = get_host_names_from_certificate(crt_file.read())

            if host_names == ['*']:
                session_kwargs['assert_hostname'] = False

        # Initializes session
        return _utl.http_session(**session_kwargs)

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
        """
        URL of the accelerator host.

        Args:
            URL (str): URL.
        """
        # Check URL
        if not url:
            raise _exc.ClientConfigurationException("Host URL is not valid.")
        self._url = url = _utl.format_url(url)

        # Updates endpoints
        for route in self._REST_API:
            self._endpoints[route] = url + self._REST_API[route]

    @property
    @_utl.memoizedmethod
    def _configuration_url(self):
        """Last configuration URL"""
        # Get last configuration, if any
        response = self._session.get(self._endpoints['start'])
        try:
            last_config = response.json()['results'][0]
        except (KeyError, IndexError, ValueError):
            return

        # The last configuration URL should be keep in order to not request
        # it to user.
        if last_config['used'] != 0:
            return last_config['url']

    @property
    def ssl_cert_crt(self):
        """
        SSL Certificate of the accelerator host.

        Returns:
            str: Path to ssl_cert_key.
        """
        return self._ssl_cert_crt

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
        self._cache['_configuration_url'] = response_dict['url']

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
