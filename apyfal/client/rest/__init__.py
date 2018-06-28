# coding=utf-8
"""Accelerator REST client.

This client allow remote accelerator control."""
import json as _json
import os as _os
import shutil as _shutil
from ast import literal_eval as _literal_eval

try:
    import pycurl as _pycurl
    _USE_PYCURL = True

    try:
        # Python 2
        from StringIO import StringIO as _BytesIO
    except ImportError:
        # Python 3
        from io import BytesIO as _BytesIO

except ImportError:
    _USE_PYCURL = False
    _pycurl = None

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
        accelerator (str): Name of the accelerator you want to initialize,
            to know the accelerator list please visit "https://accelstore.accelize.com".
        client_type (str): Type of client. Default to "REST".
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

    #: Client type
    NAME = 'REST'

    def __init__(self, accelerator, host_ip=None, *args, **kwargs):
        # Initializes OpenApi client
        self._configuration_url = None
        self._api_client = _api.ApiClient()

        # Initialize client
        _Client.__init__(self, accelerator, *args, **kwargs)

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

        # If possible use the last accelerator configuration (it can still be overwritten later)
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
            config_list = self._rest_api_configuration().configuration_list().results
        except ValueError:
            # ValueError from generated code with Swagger Codegen >= 2.3.0
            return
        if not config_list:
            return

        last_config = config_list[0]
        if last_config.used == 0:
            return

        # The last configuration URL should be keep in order to not request it to user.
        self._configuration_url = last_config.url

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
        # Skips configuration if already configured
        if not (self._configuration_url is None or datafile or parameters or host_env):
            return

        # Starts
        return _Client.start(
            self, datafile=datafile, info_dict=info_dict, host_env=host_env, **parameters)

    def _start(self, datafile, info_dict, parameters):
        """
        Client specific start implementation.

        Args:
            datafile (str): Input file.
            info_dict (bool): Returns response dict.
            parameters (dict): Parameters dict.

        Returns:
            dict or None: response.
        """
        # Configures  accelerator
        api_instance = self._rest_api_configuration()
        api_response = api_instance.configuration_create(
            parameters=_json.dumps(parameters), datafile=datafile or '')

        # Checks operation success
        config_result = _literal_eval(api_response.parametersresult)
        self._raise_for_status(config_result, "Failed to configure accelerator: ")

        api_response_read = api_instance.configuration_read(api_response.id)
        if api_response_read.inerror:
            raise _exc.ClientRuntimeException(
                "Cannot start the configuration %s" % api_response_read.url)

        # Memorizes configuration
        self._configuration_url = api_response.url

        # Returns optional response
        if info_dict:
            config_result['url_config'] = self._configuration_url
            config_result['url_instance'] = self.url
            return config_result

    def _process_openapi(self, json_parameters, datafile):
        """
        Processes using OpenApi REST API.

        Args:
            json_parameters (str): AcceleratorClient parameter as JSON
            datafile (str): Path to input datafile

        Returns:
            dict: Response from API
            bool: True if processed
        """
        api_response = self._rest_api_process().process_create(
            self._configuration_url, parameters=json_parameters, datafile=datafile)
        return api_response.id, api_response.processed

    def _process_curl(self, json_parameters, datafile):
        """
        Process using cURL (PycURL)

        Args:
            json_parameters (str): AcceleratorClient parameter as JSON
            datafile (str): Path to input datafile

        Returns:
            dict: Response from API
            bool: True if processed
        """
        # Configure cURL
        curl = _pycurl.Curl()

        post = [("parameters", json_parameters),
                ("configuration", self._configuration_url)]
        if datafile is not None:
            post.append(("datafile", (_pycurl.FORM_FILE, datafile)))

        for curl_opt in (
                (_pycurl.URL, str("%s/v1.0/process/" % self.url)),
                (_pycurl.POST, 1),
                (_pycurl.TIMEOUT, 1200),
                (_pycurl.HTTPPOST, post),
                (_pycurl.HTTPHEADER, ['Content-Type: multipart/form-data'])):
            curl.setopt(*curl_opt)

        # Process with cURL
        retries_max = 3
        retries_done = 1
        while True:
            write_buffer = _BytesIO()
            curl.setopt(_pycurl.WRITEFUNCTION, write_buffer.write)

            try:
                curl.perform()
                break

            except _pycurl.error as exception:
                if retries_done > retries_max:
                    raise _exc.ClientRuntimeException(
                        'Failed to post process request', exc=exception)
                retries_done += 1

        curl.close()

        # Get result
        content = write_buffer.getvalue().decode()

        try:
            api_response = _json.loads(content)
        except ValueError:
            raise _exc.ClientRuntimeException(
                "Response not valid", exc=content)

        if 'id' not in api_response:
            raise _exc.ClientRuntimeException(
                "Processing failed with no message (host application did not run): %s" % content)

        return api_response['id'], api_response['processed']

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
        # Check if configuration was done
        if self._configuration_url is None:
            raise _exc.ClientConfigurationException(
                "AcceleratorClient has not been configured. Use 'start' function.")

        # Checks input file presence
        if file_in and not _os.path.isfile(file_in):
            raise OSError("Could not find input file: %s", file_in)

        # Checks output directory presence, and creates it if not exists.
        if file_out:
            _utl.makedirs(_os.path.dirname(file_out), exist_ok=True)

        # Use cURL to improve performance and avoid issue with big file (https://bugs.python.org/issue8450)
        # If not available, use REST API (with limitations)
        process_function = self._process_curl if _USE_PYCURL else self._process_openapi
        api_resp_id, processed = process_function(_json.dumps(parameters), file_in)

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
                    _utl.pretty_dict(api_response.parametersresult))

            process_response = _literal_eval(api_response.parametersresult)
            self._raise_for_status(process_response, "Processing failed: ")

            # Write result file
            if file_out:
                response = _utl.http_session(https=False).get(
                    api_response.datafileresult, stream=True)
                with open(file_out, 'wb') as out_file:
                    _shutil.copyfileobj(response.raw, out_file)

        finally:
            # Process_delete api_response
            api_instance.process_delete(api_resp_id)

        return process_response

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
        api_instance.api_client.rest_client.pool_manager.connection_pool_kw['retries'] = 3
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
