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
        from StringIO import StringIO as _StringIO
    except ImportError:
        # Python 3
        from io import StringIO as _StringIO

except ImportError:
    _USE_PYCURL = False

import acceleratorAPI._utilities as _utl
import acceleratorAPI.exceptions as _exc
import acceleratorAPI.configuration as _cfg

try:
    import acceleratorAPI._swagger_client as _api
except ImportError:
    # swagger_client is dynamically generated with Swagger-codegen and
    # not provided in repository, so it is possible
    # to try to import with without have generated it first.
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
        instance_ip (str): IP or URL address of the CSP instance that host the accelerator.
        config (str or acceleratorAPI.configuration.Configuration): Configuration file path or instance.
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
                 instance_ip=None, config=None):
        self._name = accelerator
        self._access_token = None
        self._configuration_url = None
        self._url = None

        # Read configuration
        config = _cfg.create_configuration(config)
        self._client_id = config.get_default('accelize', 'client_id', overwrite=accelize_client_id)
        self._secret_id = config.get_default('accelize', 'secret_id', overwrite=accelize_secret_id)

        self._configuration_parameters = _deepcopy(self.DEFAULT_CONFIGURATION_PARAMETERS)
        self._configuration_parameters.update(config.get_default(
            'configuration', 'parameters', is_literal=True, default=dict()))

        self._process_parameters = _deepcopy(self.DEFAULT_PROCESS_PARAMETERS)
        self._process_parameters.update(config.get_default(
            'process', 'parameters', is_literal=True, default=dict()))

        # Checks if Accelize credentials are valid
        self._check_accelize_credential()

        # Initializes Swagger REST API Client
        self._api_client = _api.ApiClient()

        # Sets URL and configures
        if instance_ip:
            self.url = instance_ip

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.stop()

    def __del__(self):
        self.stop()

    def _check_accelize_credential(self):
        """
        Check user AcceleratorClient credential

        Returns:
            str: Access token.

        Raises:
            AcceleratorAuthenticationException: User credential are not valid.
        """
        if self._access_token is None:
            # Checks Client ID and secret ID presence
            if self._client_id is None or self._secret_id is None:
                raise _exc.AcceleratorConfigurationException(
                    "Accelize client ID and secret ID are mandatory.")

            # Check access and get token from server
            response = _utl.http_session().post(
                _cfg.METERING_SERVER + '/o/token/',
                data={"grant_type": "client_credentials"}, auth=(self._client_id, self._secret_id))

            if response.status_code != 200:
                raise _exc.AcceleratorAuthenticationException(
                    "Accelize authentication failed", exc=response.text)

            response.raise_for_status()

            self._access_token = _json.loads(response.text)['access_token']

        return self._access_token

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
        URL of the CSP instance that host the accelerator.

        Returns:
            str: URL
        """
        return self._url

    @url.setter
    def url(self, url):

        # Check URL
        if not url:
            raise _exc.AcceleratorConfigurationException(
                "An accelerator URL is required .")

        self._url = _utl.format_url(url)

        # Configure REST API host
        self._api_client.configuration.host = self._url

        # If possible use the last accelerator configuration (it can still be overwritten later)
        self._use_last_configuration()

    def _is_alive(self):
        """
        Check if accelerator URL exists.

        Raises:
            AcceleratorRuntimeException: If URL not alive
        """
        if self.url is None:
            raise _exc.AcceleratorRuntimeException("No accelerator running")
        if not _utl.check_url(self.url, max_retries=2):
            raise _exc.AcceleratorRuntimeException(
                gen_msg=('unable_reach_url', self._url))

    def get_csp_requirements(self, provider):
        """
        Gets accelerators requirements to use with CSP.

        Args:
            provider (str): CSP provider name.

        Returns:
            dict: AcceleratorClient requirements for CSP.
        """
        access_token = self._check_accelize_credential()

        # call WS
        headers = {"Authorization": "Bearer %s" % access_token,
                   "Content-Type": "application/json", "Accept": "application/vnd.accelize.v1+json"}

        response = _utl.http_session().get(
            _cfg.METERING_SERVER + '/auth/getlastcspconfiguration/', headers=headers)
        response.raise_for_status()
        response_config = _json.loads(response.text)

        # Get provider configuration
        try:
            provider_config = response_config[provider]
        except KeyError:
            raise _exc.AcceleratorConfigurationException(
                "CSP '%s' is not supported. Available CSP are: %s" % (
                    provider, ', '.join(response_config.keys())))

        # Get accelerator configuration
        try:
            accelerator_config = provider_config[self.name]
        except KeyError:
            raise _exc.AcceleratorConfigurationException(
                "AcceleratorClient '%s' is not supported on '%s'." % (self.name, provider))

        accelerator_config['accelerator'] = self.name
        return accelerator_config

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

    def start(self, datafile=None, info_dict=False, csp_env=None, **parameters):
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
        if not (self._configuration_url is None or datafile or parameters or csp_env):
            return

        # Checks parameters
        parameters = self._get_parameters(parameters, self._configuration_parameters)
        parameters.update({
            "env": {"client_id": self._client_id, "client_secret": self._secret_id}})
        parameters['env'].update(csp_env or dict())

        if datafile is None:
            datafile = ""

        # Configures  accelerator
        api_instance = self._rest_api_configuration()
        api_response = api_instance.configuration_create(
            parameters=_json.dumps(parameters), datafile=datafile)

        # Checks operation success
        config_result = _literal_eval(api_response.parametersresult)
        self._raise_for_status(config_result, "Failed to configure accelerator: ")

        api_response_read = api_instance.configuration_read(api_response.id)
        if api_response_read.inerror:
            raise _exc.AcceleratorRuntimeException(
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
            write_buffer = _StringIO()
            curl.setopt(_pycurl.WRITEFUNCTION, write_buffer.write)

            try:
                curl.perform()
                break

            except _pycurl.error as exception:
                if retries_done > retries_max:
                    raise _exc.AcceleratorRuntimeException(
                        'Failed to post process request', exc=exception)
                retries_done += 1

        curl.close()

        # Get result
        content = write_buffer.getvalue()

        try:
            api_response = _json.loads(content)
        except ValueError:
            raise _exc.AcceleratorRuntimeException(
                "Response not valid", exc=content)

        if 'id' not in api_response:
            raise _exc.AcceleratorRuntimeException(
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
            dict or None: Result from process operation, depending used accelerator.
            dict: Optional, only if "info_dict" is True. AcceleratorClient response.
                AcceleratorClient contain output information from  process operation.
                Take a look accelerator documentation for more information.
        """
        # TODO: Detail response dict in docstring
        # Check if configuration was done
        if self._configuration_url is None:
            raise _exc.AcceleratorConfigurationException(
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
            while processed is not True:
                api_response = api_instance.process_read(api_resp_id)
                processed = api_response.processed

            # Checks for success
            if api_response.inerror:
                raise _exc.AcceleratorRuntimeException(
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
            result = None

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
        try:
            self._is_alive()
        except _exc.AcceleratorRuntimeException:
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
            acceleratorAPI.exceptions.AcceleratorRuntimeException: Exception from arguments.
        """
        try:
            status = api_result['app']['status']
        except KeyError:
            raise _exc.AcceleratorRuntimeException('%sNo result returned' % message)
        if status:
            raise _exc.AcceleratorRuntimeException(message + api_result['app']['msg'])

    def _init_rest_api_class(self, api):
        """
        Instantiate and configure REST API class.

        Args:
            api: API class from acceleratorAPI.rest_api.swagger_client

        Returns:
            Configured instance of api class.
        """
        api_instance = api(api_client=self._api_client)
        api_instance.api_client.rest_client.pool_manager.connection_pool_kw['retries'] = 3
        return api_instance

    def _rest_api_process(self):
        """
        Instantiate Process REST API

        Returns:
            acceleratorAPI.rest_api.swagger_client.ProcessApi: class instance
        """
        return self._init_rest_api_class(_api.ProcessApi)

    def _rest_api_configuration(self):
        """
        Instantiate Configuration REST API

        Returns:
            acceleratorAPI.rest_api.swagger_client.ConfigurationApi: class instance
        """
        # /v1.0/configuration/
        return self._init_rest_api_class(_api.ConfigurationApi)

    def _rest_api_stop(self):
        """
        Instantiate Stop REST API

        Returns:
            acceleratorAPI.rest_api.swagger_client.StopApi: class instance
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
