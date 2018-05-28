# coding=utf-8
"""Accelerators"""

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
from acceleratorAPI._utilities import get_logger as _get_logger
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
            to know the authorized list please visit https://accelstore.accelize.com
        client_id (str): Accelize Client ID.
            Client Id is part of the access key you can generate on https:/accelstore.accelize.com/user/applications.
            If set will override value from configuration file.
        secret_id (str): Accelize Secret ID.
            Secret Id is part of the access key you can generate on https:/accelstore.accelize.com/user/applications.
            If set will override value from configuration file.
        url (str): AcceleratorClient URL
        config (str or acceleratorAPI.configuration.Configuration): Configuration file path or instance.
            If not set, will search it in current working directory, in current
            user "home" folder. If none found, will use default configuration values.
    """
    DEFAULT_CONFIGURATION_PARAMETERS = {"app": {
        "reset": 0,
        "enable-sw-comparison": 0,
        "logging": {"format": 1, "verbosity": 2}}}

    DEFAULT_PROCESS_PARAMETERS = {"app": {
        "reset": 0,
        "enable-sw-comparison": 0,
        "logging": {"format": 1, "verbosity": 2}}}

    def __init__(self, accelerator, client_id=None, secret_id=None, url=None, config=None):
        self._name = accelerator
        self._access_token = None
        self._configuration_url = None
        self._url = None

        # Read configuration
        config = _cfg.create_configuration(config)
        self._client_id = config.get_default('accelize', 'client_id', overwrite=client_id)
        self._secret_id = config.get_default('accelize', 'secret_id', overwrite=secret_id)

        self._configuration_parameters = config.get_default(
            'configuration', 'parameters', is_literal=True,
            default=self.DEFAULT_CONFIGURATION_PARAMETERS)
        self._process_parameters = config.get_default(
            'process', 'parameters', is_literal=True,
            default=self.DEFAULT_PROCESS_PARAMETERS)

        # Checks if Accelize credentials are valid
        self._check_accelize_credential()

        # Initializes Swagger REST API Client
        self._api_client = _api.ApiClient()

        # Sets URL and configures
        if url:
            self.url = url

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
                    "Accelize client ID and secret ID are mandatory. "
                    "Provide them in the configuration file or through function arguments.")

            # Check access and get token from server
            response = _utl.http_session().post(
                _cfg.METERING_SERVER + '/o/token/',
                data={"grant_type": "client_credentials"}, auth=(self.client_id, self.secret_id))

            if response.status_code != 200:
                raise _exc.AcceleratorAuthenticationException(
                    "Accelize authentication failed", exc=response.text)

            response.raise_for_status()

            self._access_token = _json.loads(response.text)['access_token']

        return self._access_token

    @property
    def name(self):
        """
        AcceleratorClient name

        Returns:
            str: name
        """
        return self._name

    @property
    def client_id(self):
        """
        User's Accelize client ID

        Returns:
            str: ID
        """
        return self._client_id

    @property
    def secret_id(self):
        """
        User's Accelize secret ID

        Returns:
            str: ID
        """
        return self._secret_id

    @property
    def configuration_url(self):
        """
        AcceleratorClient configuration URL

        Returns:
            str: URL
        """
        return self._configuration_url

    @property
    def url(self):
        """
        AcceleratorClient URL

        Returns:
            str: URL
        """
        return self._url

    @url.setter
    def url(self, url):

        # Check URL
        if not url:
            raise _exc.AcceleratorConfigurationException(
                "An accelerator url is required .")

        self._url = _utl.format_url(url)

        # Configure REST API host
        self._api_client.configuration.host = self._url

        # If possible use the last accelerator configuration (it can still be overwritten later)
        self._use_last_configuration()

    def is_alive(self):
        """
        Check if accelerator URL exists.

        Raises:
            AcceleratorRuntimeException: If URL not alive
        """
        if self.url is None:
            raise _exc.AcceleratorRuntimeException("No accelerator running")
        if not _utl.check_url(self.url, max_retries=2):
            raise _exc.AcceleratorRuntimeException("Failed to reach accelerator url: %s" % self.url)

    def get_requirements(self, provider):
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

    def start(self, datafile=None, accelerator_parameters=None, csp_env=None):
        """
        Create an AcceleratorClient configuration.

        Args:
            datafile (str): Depending on the accelerator (like for HyperFiRe),
                a configuration need to be loaded before a process can be run.
                In such case please define the path of the configuration file
                (for HyperFiRe the corpus file path).
            accelerator_parameters (dict): If set will overwrite the value content in the configuration file
                Parameters can be forwarded to the accelerator for the configuration step using these parameters.
                Take a look accelerator documentation for more information.
            csp_env:

        Returns:
            dict: AcceleratorClient response. Contain output information from configuration operation.
                Take a look accelerator documentation for more information.
        """
        # TODO: Detail response dict in docstring
        # Check parameters
        if accelerator_parameters is None:
            accelerator_parameters = self._configuration_parameters

        parameters = {
            "env": {
                "client_id": self.client_id,
                "client_secret": self.secret_id}}
        if csp_env:
            parameters['env'].update(csp_env)
        parameters.update(accelerator_parameters)

        if datafile is None:
            datafile = ""

        # Configure  accelerator
        api_instance = self._rest_api_configuration()
        api_response = api_instance.configuration_create(parameters=_json.dumps(parameters), datafile=datafile)
        _get_logger().debug("configuration_create api_response:\n%s", api_response)

        config_result = _literal_eval(api_response.parametersresult)
        self._raise_for_status(config_result, "Configuration of accelerator failed: ")

        config_result['url_config'] = self._configuration_url = api_response.url
        config_result['url_instance'] = self.url

        api_response_read = api_instance.configuration_read(api_response.id)
        if api_response_read.inerror:
            raise _exc.AcceleratorRuntimeException("Cannot start the configuration %s" % api_response_read.url)

        return config_result

    def _process_swagger(self, accelerator_parameters, datafile):
        """
        Process using Swagger REST API.

        Args:
            accelerator_parameters (str): AcceleratorClient parameter as JSON
            datafile (str): Path to input datafile

        Returns:
            dict: Response from API
            bool: True if processed
        """
        api_response = self._rest_api_process().process_create(
            self.configuration_url, parameters=accelerator_parameters, datafile=datafile)
        return api_response.id, api_response.processed

    def _process_curl(self, accelerator_parameters, datafile):
        """
        Process using cURL (PycURL)

        Args:
            accelerator_parameters (str): AcceleratorClient parameter as JSON
            datafile (str): Path to input datafile

        Returns:
            dict: Response from API
            bool: True if processed
        """
        # Configure cURL
        curl = _pycurl.Curl()

        post = [("parameters", accelerator_parameters),
                ("configuration", self.configuration_url)]
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

    def process(self, file_in, file_out, accelerator_parameters=None):
        """
        Process a file with accelerator.

        Args:
            file_out (str): Path to the file you want to process.
            file_in (str): Path where you want the processed file will be stored.
            accelerator_parameters (dict): If set will overwrite the value content in the configuration file Parameters
                an be forwarded to the accelerator for the process step using these parameters.
                Take a look accelerator documentation for more information.

        Returns:
            dict: AcceleratorClient response. Contain output information from process operation.
                Take a look accelerator documentation for more information.
        """
        # TODO: Detail response dict in docstring
        # Check if configuration was done
        if self.configuration_url is None:
            raise _exc.AcceleratorConfigurationException(
                "AcceleratorClient has not been configured. Use 'start' function.")

        # Checks input file presence
        if file_in and not _os.path.isfile(file_in):
            raise OSError("Could not find input file: %s", file_in)

        # Checks output directory presence, and creates it if not exists.
        if file_out:
            _utl.makedirs(_os.path.dirname(file_out), exist_ok=True)

        # Configure processing
        if accelerator_parameters is None:
            accelerator_parameters = self._process_parameters

        # Use cURL to improve performance and avoid issue with big file (https://bugs.python.org/issue8450)
        # If not available, use REST API (with limitations)
        process_function = self._process_curl if _USE_PYCURL else self._process_swagger
        api_resp_id, processed = process_function(_json.dumps(accelerator_parameters), file_in)

        # Get result
        api_instance = self._rest_api_process()
        try:
            while processed is not True:
                api_response = api_instance.process_read(api_resp_id)
                processed = api_response.processed

            if api_response.inerror:
                raise _exc.AcceleratorRuntimeException(
                    "Failed to process data: %s" % _utl.pretty_dict(api_response.parametersresult))

            process_result = _literal_eval(api_response.parametersresult)
            self._raise_for_status(process_result, "Processing failed: ")

            response = _utl.http_session().get(api_response.datafileresult, stream=True)
            with open(file_out, 'wb') as out_file:
                _shutil.copyfileobj(response.raw, out_file)

        finally:
            # Process_delete api_response
            api_instance.process_delete(api_resp_id)

        return process_result

    def stop(self):
        """
        Stop your accelerator session.

        Returns:
            dict: AcceleratorClient response. Contain output information from stop operation.
                Take a look accelerator documentation for more information.
        """
        # TODO: Detail response dict in docstring
        try:
            self.is_alive()
        except _exc.AcceleratorRuntimeException:
            # No AcceleratorClient to stop
            return None
        try:
            return self._rest_api_stop().stop_list()
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
