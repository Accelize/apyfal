# coding=utf-8
"""Accelerators"""

import os
import shutil
import ast
import json

try:
    import pycurl
    _USE_PYCURL = True

    try:
        # Python 2
        from StringIO import StringIO as _StringIO
    except ImportError:
        # Python 3
        from io import StringIO as _StringIO

except ImportError:
    _USE_PYCURL = False

from acceleratorAPI import logger
import acceleratorAPI._utilities  as _utl
import acceleratorAPI.exceptions as _exc
import acceleratorAPI.configuration as _cfg
import acceleratorAPI.rest_api.swagger_client as _swc



class Accelerator(object):
    """
    End user API based on the openAPI Accelize accelerator

    Args:
        accelerator (str): Accelerator name.
        client_id (str): Accelize user's client ID, uses value from config if not specified.
        secret_id (str): Accelize user's secret ID, uses value from config if not specified.
        url (str): Accelerator URL
        config (str or acceleratorAPI.configuration.Configuration): Configuration file path or instance
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

        # Checks mandatory configuration values
        if self._client_id is None or self._secret_id is None:
            raise _exc.AcceleratorConfigurationException(
                "Accelize client ID and secret ID are mandatory. "
                "Provide them in the configuration file or through function arguments.")

        # Checks if Accelize credentials are valid
        self._check_accelize_credential()

        # A regular API has fixed url. In our case we want to change it dynamically.
        self._api_configuration = _swc.Configuration()
        self.url = url
        self._accelerator_configuration_url = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.stop_accelerator()

    def __del__(self):
        self.stop_accelerator()

    def _check_accelize_credential(self):
        """
        Check user Accelerator credential

        Raises:
            AcceleratorAuthenticationException: User credential are not valid.
        """
        response = _utl.https_session().post(
            'https://master.metering.accelize.com/o/token/',
            data={"grant_type": "client_credentials"}, auth=(self.client_id, self.secret_id))

        if response.status_code != 200:
            raise _exc.AcceleratorAuthenticationException(
                "Accelize authentication failed (%d): %s" % (response.status_code, response.text))

        logger.info("Accelize authentication for '%s' is successful", self._name)

    @property
    def name(self):
        """
        Accelerator name

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
        return self._accelerator_configuration_url

    @property
    def url(self):
        """
        Accelerator URL

        Returns:
            str: URL
        """
        return self._api_configuration.host

    @url.setter
    def url(self, url):
        self._api_configuration.host = _utl.format_url(url)

    def is_alive(self):
        """
        Check if accelerator URL exists.

        Raises:
            AcceleratorRuntimeException: If URL not alive
        """
        if self.url is None:
            raise _exc.AcceleratorRuntimeException("No accelerator running")
        if not _utl.check_url(self.url, 10, logger=logger):
            raise _exc.AcceleratorRuntimeException("Failed to reach accelerator url: %s" % self.url)

    def get_accelerator_requirements(self, provider):
        session = _utl.https_session()
        response = session.post('https://master.metering.accelize.com/o/token/',
                                data={"grant_type": "client_credentials"},
                                auth=(self.client_id, self.secret_id))
        logger.debug("Accelize token answer: %s", response.text)
        response.raise_for_status()

        if response.status_code == 200:
            # call WS
            answer_token = json.loads(response.text)
            headers = {"Authorization": "Bearer %s" % answer_token['access_token'],
                       "Content-Type": "application/json", "Accept": "application/vnd.accelize.v1+json"}
            response = session.get(
                'https://master.metering.accelize.com/auth/getlastcspconfiguration/', headers=headers)
            logger.debug("Accelize config answer: %s, status: %s", response.text, str(response.status_code))
            response.raise_for_status()

            configuration_accelerator = json.loads(response.text)
            logger.debug("Accelerator requirements:\n%s", _utl.pretty_dict(configuration_accelerator))

            # Check configuration with CSP
            if provider not in configuration_accelerator:
                raise _exc.AcceleratorConfigurationException(
                    "CSP '%s' is not supported. Available CSP are: %s" % (
                        provider, ', '.join(configuration_accelerator.keys())))

            if self._name not in configuration_accelerator[provider]:
                raise _exc.AcceleratorConfigurationException(
                    "Accelerator '%s' is not supported on '%s'." % (self._name, provider))

            info = configuration_accelerator[provider][self._name]
            info['accelerator'] = self._name
            return info

    def get_accelerator_configuration_list(self):
        # Check URL
        if self.url is None:
            raise _exc.AcceleratorConfigurationException(
                "An accelerator url is required to get the list of configurations.")

        # Create an instance of the API class
        api_instance = self._rest_api_configuration()

        # Get configuration list
        logger.debug("Get list of configurations...")
        config_list = api_instance.configuration_list().results

        return config_list

    def use_last_configuration(self):
        # Get last configuration, if any
        config_list = self.get_accelerator_configuration_list()
        if not config_list:
            logger.info("Accelerator has not been configured yet.")
            return False

        last_config = config_list[0]
        logger.debug("Last recorded configuration: Url:%s, Used:%d", last_config.url, last_config.used)
        if last_config.used == 0:
            logger.info("Accelerator has no active configuration. It needs to be configured before being used.")
            return False

        logger.info("Accelerator is loaded with configuration: %s", last_config.url)

        # The last configuration URL should be keep in order to not request it to user.
        self._accelerator_configuration_url = last_config.url
        return True

    def start_accelerator(self, datafile=None, accelerator_parameters=None, csp_env=None):
        """
        Create an Accelerator configuration.

        Args:
            datafile:
            accelerator_parameters:
            csp_env:

        Returns:

        """
        # Check parameters
        if accelerator_parameters is None:
            logger.debug("Using default configuration parameters")
            accelerator_parameters = self._configuration_parameters

        envserver = {"client_id": self.client_id, "client_secret": self.secret_id}
        envserver.update(csp_env)
        parameters = {"env": envserver}
        parameters.update(accelerator_parameters)
        logger.debug("parameters = \n%s", json.dumps(parameters, indent=4))

        logger.debug("datafile = %s", datafile)
        if datafile is None:
            datafile = ""

        # Configure  accelerator
        logger.info("Configuring accelerator...")

        api_instance = self._rest_api_configuration()
        api_response = api_instance.configuration_create(parameters=json.dumps(parameters), datafile=datafile)
        logger.debug("configuration_create api_response:\n%s", api_response)

        config_result = ast.literal_eval(api_response.parametersresult)
        self._raise_for_status(config_result, "Configuration of accelerator failed: ")

        config_result['url_config'] = self._accelerator_configuration_url = api_response.url
        config_result['url_instance'] = self.url

        logger.debug("status: %s", config_result['app']['status'])
        logger.debug("msg:\n%s", config_result['app']['msg'])

        api_response_read = api_instance.configuration_read(api_response.id)
        if api_response_read.inerror:
            raise _exc.AcceleratorRuntimeException("Cannot start the configuration %s" % api_response_read.url)

        return config_result

    def process_file(self, file_in, file_out, accelerator_parameters=None):

        # Check if configuration was done
        if self._accelerator_configuration_url is None:
            raise _exc.AcceleratorConfigurationException(
                "Accelerator has not been configured. Use 'start_accelerator' function.")

        # Checks input file presence
        if file_in and not os.path.isfile(file_in):
            raise OSError("Could not find input file: %s", file_in)

        # Checks output directory presence, and creates it if not exists.
        if file_out:
            try:
                os.makedirs(os.path.dirname(file_out))
            except OSError:
                if not os.path.isdir(os.path.dirname(file_out)):
                    raise

        # Configure processing
        if accelerator_parameters is None:
            logger.debug("Using default processing parameters")
            accelerator_parameters = self._process_parameters
        logger.debug("Using configuration: %s", self._accelerator_configuration_url)
        datafile = file_in  # file | If needed, file to be processed by the accelerator. (optional)

        api_instance = self._rest_api_process()

        # Bypass REST API because upload issue with big file using python https://bugs.python.org/issue8450
        if _USE_PYCURL:
            logger.debug("pycurl process=%s datafile=%s", self._accelerator_configuration_url, datafile)
            retries_max = 3
            retries_done = 1

            post = [("parameters", json.dumps(accelerator_parameters)),
                    ("configuration", self._accelerator_configuration_url)]
            if file_in is not None:
                post.append(("datafile", (pycurl.FORM_FILE, file_in)))

            while True:
                storage = _StringIO()
                curl = pycurl.Curl()
                curl.setopt(curl.WRITEFUNCTION, storage.write)
                curl.setopt(curl.URL, str("%s/v1.0/process/" % self.url))
                curl.setopt(curl.POST, 1)
                curl.setopt(curl.HTTPPOST, post)
                curl.setopt(curl.HTTPHEADER, ['Content-Type: multipart/form-data'])
                try:
                    curl.perform()
                    break

                except pycurl.error as exception:
                    logger.error("Failed to post process request after %d/%d attempts because of: %s", retries_done,
                                 retries_max, exception)
                    if retries_done > retries_max:
                        raise exception
                    retries_done += 1

                finally:
                    curl.close()

            content = storage.getvalue()
            logger.debug("pycurl process: %s", content)
            api_response = json.loads(content)
            if 'id' not in api_response:
                raise _exc.AcceleratorRuntimeException(
                    "Processing failed with no message (host application did not run).")

            api_resp_id = api_response['id']
            processed = api_response['processed']

        # Use REST API (with limitations) if pycurl is not available
        else:
            logger.debug("process_create process=%s datafile=%s", self._accelerator_configuration_url, datafile)
            api_response = api_instance.process_create(self._accelerator_configuration_url,
                                                       parameters=json.dumps(accelerator_parameters),
                                                       datafile=datafile)
            api_resp_id = api_response.id
            processed = api_response.processed

        # Get result
        try:
            while processed is not True:
                api_response = api_instance.process_read(api_resp_id)
                processed = api_response.processed

            if api_response.inerror:
                raise _exc.AcceleratorRuntimeException(
                    "Failed to process data: %s" % _utl.pretty_dict(api_response.parametersresult))

            process_result = ast.literal_eval(api_response.parametersresult)
            self._raise_for_status(process_result, "Processing failed: ")

            logger.debug("Process status: %s", process_result['app']['status'])
            logger.debug("Process msg:\n%s", process_result['app']['msg'])

            response = _utl.https_session().get(api_response.datafileresult, stream=True)
            with open(file_out, 'wb') as out_file:
                shutil.copyfileobj(response.raw, out_file)

        finally:
            logger.debug("process_delete api_response: %s", api_resp_id)
            api_instance.process_delete(api_resp_id)

        return process_result

    def stop_accelerator(self):
        try:
            self.is_alive()
        except _exc.AcceleratorRuntimeException:
            # No Accelerator to stop
            return None

        logger.debug("Stopping accelerator '%s'", self.name)

        stop_result = self._rest_api_stop().stop_list()
        self._raise_for_status(stop_result, "Stopping accelerator failed: ")
        return stop_result

    @staticmethod
    def _raise_for_status(api_result, message=""):
        try:
            status = api_result['app']['status']
        except KeyError:
            raise _exc.AcceleratorRuntimeException(message + 'No result returned')
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
        api_instance = api(api_client=self._api_configuration.api_client)
        api_instance.api_client.rest_client.pool_manager.connection_pool_kw['retries'] = 3
        return api_instance

    def _rest_api_process(self):
        """
        Instantiate Process REST API

        Returns:
            acceleratorAPI.rest_api.swagger_client.ProcessApi: class instance
        """
        return self._init_rest_api_class(_swc.ProcessApi)

    def _rest_api_configuration(self):
        """
        Instantiate Configuration REST API

        Returns:
            acceleratorAPI.rest_api.swagger_client.ConfigurationApi: class instance
        """
        # /v1.0/configuration/
        return self._init_rest_api_class(_swc.ConfigurationApi)

    def _rest_api_stop(self):
        """
        Instantiate Stop REST API

        Returns:
            acceleratorAPI.rest_api.swagger_client.StopApi: class instance
        """
        # /v1.0/stop
        return self._init_rest_api_class(_swc.StopApi)
