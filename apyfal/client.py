# coding=utf-8
"""Accelerators"""

from copy import deepcopy as _deepcopy
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
import apyfal.configuration as _cfg

try:
    import apyfal._swagger_client as _api
except ImportError:  # Swagger_codegen need to be run first
    if not _os.path.isfile(_os.path.join(
            _os.path.dirname(__file__), '_swagger_client/__init__.py')):
        raise ImportError(
            'Swagger client not found, please generate it '
            'with "setup.py swagger_codegen"')
    raise


class AcceleratorClient(object):
    """
    End user API based on the openAPI Accelize accelerator

    Args:
        accelerator (str): Name of the accelerator you want to initialize,
            to know the accelerator list please visit "https://accelstore.accelize.com".
        accelize_client_id (str): Accelize Client ID.
            Client ID is part of the access key you can generate on
            "https:/accelstore.accelize.com/user/applications".
        accelize_secret_id (str): Accelize Secret ID. Secret ID come with client_id.
        host_ip (str): IP or URL address of the accelerator host.
        config (str or apyfal.configuration.Configuration): Configuration file path or instance.
            If not set, will search it in current working directory, in current
            user "home" folder. If none found, will use default configuration values
    """
    DEFAULT_CONFIGURATION_PARAMETERS = {"app": {
        "reset": 0,
        "enable-sw-comparison": 0,
        "logging": {"format": 1, "verbosity": 2},
        "specific": {}}}

    DEFAULT_PROCESS_PARAMETERS = {"app": {
        "reset": 0,
        "enable-sw-comparison": 0,
        "logging": {"format": 1, "verbosity": 2},
        "specific": {}}}

    def __init__(self, accelerator, accelize_client_id=None, accelize_secret_id=None,
                 host_ip=None, config=None):
        self._name = accelerator
        self._configuration_url = None
        self._url = None
        self._stopped = False

        # Read configuration
        self._config = config = _cfg.create_configuration(config)
        self._client_id = config['accelize'].set('client_id', accelize_client_id)
        self._secret_id = config['accelize'].set('secret_id', accelize_secret_id)

        self._configuration_parameters = self._load_configuration(
            self.DEFAULT_CONFIGURATION_PARAMETERS, 'configuration')
        self._process_parameters = self._load_configuration(
            self.DEFAULT_PROCESS_PARAMETERS, 'process')

        # Initializes Swagger REST API Client
        self._api_client = _api.ApiClient()

        # Sets URL and configures
        if host_ip:
            self.url = host_ip

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.stop()

    def __del__(self):
        self.stop()

    @property
    def name(self):
        """
        Accelerator name

        Returns:
            str: name
        """
        return self._name

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
        Create an AcceleratorClient configuration.

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
        # TODO: Detail response dict in docstring

        # Skips configuration if already configured
        if not (self._configuration_url is None or datafile or parameters or host_env):
            return

        # Checks parameters
        parameters = self._get_parameters(parameters, self._configuration_parameters)
        parameters.update({
            "env": {"client_id": self._client_id, "client_secret": self._secret_id}})
        parameters['env'].update(host_env or dict())

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

    def _process_swagger(self, json_parameters, datafile):
        """
        Process using Swagger REST API.

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

    def process(self, file_in=None, file_out=None, info_dict=False, **parameters):
        """
        Process a file with accelerator.

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
        # TODO: Detail response dict in docstring
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

        # Configure processing
        parameters = self._get_parameters(parameters, self._process_parameters)

        # Use cURL to improve performance and avoid issue with big file (https://bugs.python.org/issue8450)
        # If not available, use REST API (with limitations)
        process_function = self._process_curl if _USE_PYCURL else self._process_swagger
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

        # Get result from response and returns
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
        Stop your accelerator session.

        Args:
            info_dict (bool): If True, returns a dict containing information on
                stop operation.

        Returns:
            dict: Optional, only if "info_dict" is True. AcceleratorClient response.
                AcceleratorClient contain output information from  stop operation.
                Take a look to accelerator documentation for more information.
        """
        # TODO: Detail response dict in docstring

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
            result = self._rest_api_stop().stop_list()
            if info_dict:
                return result
        except _api.rest.ApiException:
            pass

    @staticmethod
    def _raise_for_status(api_result, message=""):
        """
        Check REST API results and raise exception in case of error.

        Args:
            api_result (dict): Result from REST API.
            message (str): Optional exception message to add before REST API message.

        Raises:
            apyfal.exceptions.ClientRuntimeException: Exception from arguments.
        """
        try:
            status = api_result['app']['status']
        except KeyError:
            raise _exc.ClientRuntimeException('%sNo result returned' % message)
        if status:
            raise _exc.ClientRuntimeException(message + api_result['app']['msg'])

    def _init_rest_api_class(self, api):
        """
        Instantiate and configure REST API class.

        Args:
            api: API class from apyfal.rest_api.swagger_client

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
            apyfal.rest_api.swagger_client.ProcessApi: class instance
        """
        return self._init_rest_api_class(_api.ProcessApi)

    def _rest_api_configuration(self):
        """
        Instantiate Configuration REST API

        Returns:
            apyfal.rest_api.swagger_client.ConfigurationApi: class instance
        """
        # /v1.0/configuration/
        return self._init_rest_api_class(_api.ConfigurationApi)

    def _rest_api_stop(self):
        """
        Instantiate Stop REST API

        Returns:
            apyfal.rest_api.swagger_client.StopApi: class instance
        """
        # /v1.0/stop
        return self._init_rest_api_class(_api.StopApi)

    @staticmethod
    def _get_parameters(parameters, default_parameters):
        """
        Gets parameters from different sources, and merge them together.

        If 'parameters' contain a key named 'parameters', it will be
        read as a full parameter dict, or JSON literal or JSON file.

        Other keys from 'parameters' will be merged to the 'specific'
        section of the result dict.

        Args:
            parameters (dict): parameters
            default_parameters (dict): default parameters

        Returns:
            dict : parameters.
        """
        # Takes default parameters as basis
        result = _deepcopy(default_parameters)

        # Gets parameters from included JSON file
        try:
            json_parameters = parameters.pop('parameters')
        except KeyError:
            pass
        else:
            # Reads JSON parameter from file or literal
            if isinstance(json_parameters, str):
                # JSON literal
                if json_parameters.startswith('{'):
                    json_parameters = _json.loads(json_parameters)

                # JSON file
                else:
                    with open(json_parameters, 'rt') as json_file:
                        json_parameters = _json.load(json_file)

            # Merges to result
            result.update(json_parameters)

        # Merges other parameters to specific section of parameters
        try:
            specific = result['app']['specific']
        except KeyError:
            specific = result['app']['specific'] = dict()
        specific.update(parameters)

        return result

    def _load_configuration(self, default_parameters, section):
        """Load parameters from configuration.

        Args:
            default_parameters (dict): default parameters
            section (str): Section in configuration."""
        # Load default parameters
        parameters = _deepcopy(default_parameters)

        # Update with configuration
        config = self._config['%s.%s' % (section, self._name)]
        _utl.recursive_update(
            parameters, config.get_literal('parameters') or {})
        return parameters
