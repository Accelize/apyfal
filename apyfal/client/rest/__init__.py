# coding=utf-8
"""Accelerator REST client.

This client allow remote accelerator control."""
import json as _json
import os as _os
import shutil as _shutil
from ast import literal_eval as _literal_eval

from requests_toolbelt.multipart.encoder import (
    MultipartEncoder as _MultipartEncoder)

import apyfal._utilities as _utl
import apyfal.exceptions as _exc
from apyfal.client import AcceleratorClient as _Client

try:
    from apyfal.client.rest import _openapi as _api
except ImportError:  # OpenAPI client need to be generated first
    if not _os.path.isfile(_os.path.join(
            _os.path.dirname(__file__), '_openapi/__init__.py')):
        raise ImportError(
            'OpenAPI client not found, please generate it '
            'with "setup.py swagger_codegen"')
    raise


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
    _PARAMETER_IO_FORMAT = {'file_in': 'stream', 'file_out': 'stream'}

    def __init__(self, accelerator=None, host_ip=None, *args, **kwargs):
        # Initialize client
        _Client.__init__(self, accelerator=accelerator, *args, **kwargs)

        # Initializes HTTP client
        self._configuration_url = None
        self._api_client = _api.ApiClient()

        self._session = _utl.http_session(https=False)

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

        self._url = _utl.format_url(url)

        # Configure REST API host
        self._api_client.configuration.host = self._url

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
        try:
            config_list = self._rest_api_configuration().configuration_list(
            ).results
        except ValueError:
            # ValueError from generated code with Swagger Codegen >= 2.3.0
            return
        if not config_list:
            return

        last_config = config_list[0]
        if last_config.used == 0:
            return

        # The last configuration URL should be keep in order to not request
        # it to user.
        self._configuration_url = last_config.url

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
        # Configures  accelerator
        api_instance = self._rest_api_configuration()
        api_response = api_instance.configuration_create(
            parameters=_json.dumps(parameters), datafile=datafile or '')

        # Checks operation success
        config_result = _literal_eval(api_response.parametersresult)

        api_response_read = api_instance.configuration_read(api_response.id)
        if api_response_read.inerror:
            raise _exc.ClientRuntimeException(
                "Cannot start the configuration %s" % api_response_read.url)

        # Memorizes configuration
        self._configuration_url = api_response.url

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
        multipart = _MultipartEncoder(fields={
            'parameters': _json.dumps(parameters),
            'configuration': self._configuration_url,
            'datafile': ('file_in', file_in, 'application/octet-stream')})

        response = self._session.post(
            "%s/v1.0/process/" % self.url, data=multipart,
            headers={'Content-Type': multipart.content_type})

        # Check response
        try:
            api_response = response.json()
        except ValueError:
            raise _exc.ClientRuntimeException(
                "Response not valid", exc=response.text)

        try:
            api_resp_id = api_response['id']
        except KeyError:
            raise _exc.ClientRuntimeException(
                "Processing failed with no message "
                "(host application did not run): %s" % response.text)

        # Get result
        api_instance = self._rest_api_process()
        try:
            while True:
                api_response = api_instance.process_read(api_resp_id)
                processed = api_response.processed
                if processed is True:
                    break

            # Checks for success
            if api_response.inerror:
                raise _exc.ClientRuntimeException(
                    "Failed to process data: %s" %
                    api_response.parametersresult)

            # Write result file
            if file_out:
                response = self._session.get(
                    api_response.datafileresult, stream=True)
                _shutil.copyfileobj(response.raw, file_out)

            # Get response
            return _literal_eval(api_response.parametersresult)

        finally:
            # Process_delete api_response
            api_instance.process_delete(api_resp_id)

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

        try:
            return self._rest_api_stop().stop_list()
        except _api.rest.ApiException:
            pass

    def _init_rest_api_class(self, api):
        """
        Instantiate and configure REST API class.

        Args:
            api: API class from apyfal.client.rest._openapi

        Returns:
            Configured instance of API class.
        """
        api_instance = api(api_client=self._api_client)
        api_instance.api_client.rest_client.pool_manager.connection_pool_kw[
            'retries'] = 3
        return api_instance

    def _rest_api_process(self):
        """
        Instantiate Process REST API

        Returns:
            apyfal.client.rest._openapi.ProcessApi: class instance
        """
        return self._init_rest_api_class(_api.ProcessApi)

    def _rest_api_configuration(self):
        """
        Instantiate Configuration REST API

        Returns:
            apyfal.client.rest._openapi.ConfigurationApi: class instance
        """
        # /v1.0/configuration/
        return self._init_rest_api_class(_api.ConfigurationApi)

    def _rest_api_stop(self):
        """
        Instantiate Stop REST API

        Returns:
            apyfal.client.rest._openapi.StopApi: class instance
        """
        # /v1.0/stop
        return self._init_rest_api_class(_api.StopApi)
