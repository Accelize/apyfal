# coding=utf-8
__version__ = "2.0.3"

import ast
import json
import os
import shutil
import socket

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

import acceleratorAPI.rest_api.swagger_client as _swagger_client

import acceleratorAPI.utilities as _utils
from acceleratorAPI.configuration import create_configuration as _create_configuration

# Initialize logger
logger = _utils.init_logger("acceleratorAPI", __file__)

from acceleratorAPI.csp import CSPClassFactory as _CSPClassFactory

TERM = 0
STOP = 1
KEEP = 2


class AcceleratorException(Exception):
    """
    Generic accelerator related exception.
    """


class AcceleratorAuthenticationException(AcceleratorException):
    """
    Error while trying to authenticate user.
    """


class AcceleratorConfigurationException(AcceleratorException):
    """
    Error with Accelerator configuration.
    """


class AcceleratorRuntimeException(AcceleratorException):
    """
    Error with Accelerator running.
    """


class _SignalHandlerAccelerator(object):
    """
    Signal handler for instances

    Args:
        parent (AcceleratorClass): Parent instance.
    """
    _SOCKET_TIMEOUT = 1200  # seconds

    def __init__(self, parent):
        self._parent = parent
        self._set_signals()
        self._default_socket_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(self._SOCKET_TIMEOUT)

    @property
    def _stop_mode(self):
        return self._parent.stop_mode

    @property
    def _csp(self):
        return self._parent.csp_instance

    def _set_signals(self):
        """
        Set a list of interrupt signals to be handled asynchronously
        """
        # Lazy import since only used with AcceleratorClass
        import signal

        for signal_name in ('SIGTERM', 'SIGINT', 'SIGQUIT'):
            # Check signal exist on current OS before setting it
            if hasattr(signal, signal_name):
                signal.signal(getattr(signal, signal_name), self.signal_handler_accelerator)

    def signal_handler_accelerator(self, _signo="", _stack_frame="", exit=True):
        """
        Try to stop all instances running or inform user.

        Args:
            _signo:
            _stack_frame:
            exit (bool):
        """
        try:
            if self._csp is None:
                logger.debug("There is no registered instance to stop")
                return
            if self._stop_mode == KEEP or not self._csp.get_instance_csp():
                logger.warning("###########################################################")
                logger.warning("## Instance with URL %s (ID=%s) is still running!",
                               self._csp.instance_url, self._csp.instance_id)
                logger.warning("## Make sure you will stop manually the instance.")
                logger.warning("###########################################################")
            else:
                terminate = True if self._stop_mode == TERM else False
                self._csp.stop_instance_csp(terminate)
        finally:
            logger.info("More detailed messages can be found in %s", logger.filename)
            if exit:
                socket.setdefaulttimeout(self._default_socket_timeout)
                logger.info("Accelerator API Closed properly")
                os._exit(0)


class AcceleratorApiClass(object):
    """
    End user API based on the openAPI Accelize accelerator

    Args:
        accelerator (str): Accelerator name.
        client_id (str): Accelize user's client ID, uses value from config if not specified.
        secret_id (str): Accelize user's secret ID, uses value from config if not specified.
        url (str): Accelerator URL
        config (str or acceleratorAPI.configuration.Configuration): Configuration file path or instance
    """

    def __init__(self, accelerator, client_id=None, secret_id=None, url=None, config=None):
        self._name = accelerator

        # A regular API has fixed url. In our case we want to change it dynamically.
        self._api_configuration = _swagger_client.Configuration()
        self.url = url
        self._accelerator_configuration_url = None

        # Initializes configuration
        self._config = _create_configuration(config)
        self._config.set_not_none('accelize', 'client_id', client_id)
        self._config.set_not_none('accelize', 'secret_id', secret_id)

        # Checks mandatory configuration values
        if not self._config.is_valid(('accelize', 'client_id'), ('accelize', 'secret_id')):
            raise AcceleratorConfigurationException(
                "Accelize client ID and secret ID are mandatory. "
                "Provide them in the configuration file or through function arguments.")

    def check_accelize_credential(self):
        """
        Check user Accelerator credential

        Raises:
            AcceleratorAuthenticationException: User credential are not valid.
        """
        response = _utils.https_session().post(
            'https://master.metering.accelize.com/o/token/',
            data={"grant_type": "client_credentials"}, auth=(self.client_id, self.secret_id))

        if response.status_code != 200:
            raise AcceleratorAuthenticationException(
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
        return self._config.get('accelize', 'client_id')

    @property
    def secret_id(self):
        """
        User's Accelize secret ID

        Returns:
            str: ID
        """
        return self._config.get('accelize', 'secret_id')

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
        self._api_configuration.host = url

    def get_accelerator_requirements(self, provider):
        session = _utils.https_session()
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
            logger.debug("Accelerator requirements:\n%s", _utils.pretty_dict(configuration_accelerator))

            # Check configuration with CSP
            if provider not in configuration_accelerator:
                raise AcceleratorConfigurationException(
                    "CSP '%s' is not supported. Available CSP are: %s" % (
                        provider, ', '.join(configuration_accelerator.keys())))

            if self._name not in configuration_accelerator[provider]:
                raise AcceleratorConfigurationException(
                    "Accelerator '%s' is not supported on '%s'." % (self._name, provider))

            info = configuration_accelerator[provider][self._name]
            info['accelerator'] = self._name
            return info

    def get_accelerator_configuration_list(self):
        # Check URL
        if self.url is None:
            raise AcceleratorConfigurationException(
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
            accelerator_parameters = ast.literal_eval(self._config.get("configuration", "parameters"))

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

        api_resp_id = api_response.id
        self._accelerator_configuration_url = api_response.url

        dictparameters = ast.literal_eval(api_response.parametersresult)
        dictparameters['url_config'] = api_response.url
        dictparameters['url_instance'] = self.url

        logger.debug("status: %s", dictparameters['app']['status'])
        logger.debug("msg:\n%s", dictparameters['app']['msg'])

        api_response_read = api_instance.configuration_read(api_resp_id)
        if api_response_read.inerror:
            raise AcceleratorRuntimeException("Cannot start the configuration %s" % api_response_read.url)

        return dictparameters

    def process_file(self, file_in, file_out, accelerator_parameters=None):

        if self._accelerator_configuration_url is None:
            raise AcceleratorConfigurationException(
                "Accelerator has not been configured. Use 'start_accelerator' function.")

        if accelerator_parameters is None:
            logger.debug("Using default processing parameters")
            accelerator_parameters = ast.literal_eval(self._config.get("process", "parameters"))
        logger.debug("Using configuration: %s", self._accelerator_configuration_url)
        datafile = file_in  # file | If needed, file to be processed by the accelerator. (optional)

        api_instance = self._rest_api_process()

        # Bypass REST API because upload issue with big file using python https://bugs.python.org/issue8450
        if _USE_PYCURL:
            logger.debug("pycurl process=%s datafile=%s", self._accelerator_configuration_url, datafile)
            retries_max = 3
            retries_done = 1
            while True:
                try:
                    storage = _StringIO()
                    curl = pycurl.Curl()
                    curl.setopt(curl.WRITEFUNCTION, storage.write)
                    curl.setopt(curl.URL, "%s/v1.0/process/" % self.url)
                    curl.setopt(curl.POST, 1)
                    post = [("parameters", json.dumps(accelerator_parameters)),
                            ("configuration", self._accelerator_configuration_url)]
                    if file_in is not None:
                        post.append(("datafile", (curl.FORM_FILE, file_in)))
                    curl.setopt(curl.HTTPPOST, post)
                    curl.setopt(curl.HTTPHEADER, ['Content-Type: multipart/form-data'])
                    curl.perform()
                    break

                except Exception as exception:
                    logger.error("Failed to post process request after %d/%d attempts because of: %s", retries_done,
                                 retries_max, str(exception))
                    if retries_done > retries_max:
                        raise exception
                    retries_done += 1

                finally:
                    curl.close()

            content = storage.getvalue()
            logger.debug("pycurl process: %s", content)
            api_response = json.loads(content)
            if 'id' not in api_response:
                raise AcceleratorRuntimeException(
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
                raise AcceleratorRuntimeException(
                    "Failed to process data: %s" % _utils.pretty_dict(api_response.parametersresult))

            dictparameters = ast.literal_eval(api_response.parametersresult)
            logger.debug("Process status: %s", dictparameters['app']['status'])
            logger.debug("Process msg:\n%s", dictparameters['app']['msg'])

            response = _utils.https_session().get(api_response.datafileresult, stream=True)
            with open(file_out, 'wb') as out_file:
                shutil.copyfileobj(response.raw, out_file)

        finally:
            logger.debug("process_delete api_response: %s", api_resp_id)
            api_instance.process_delete(api_resp_id)

        return dictparameters

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
        return self._init_rest_api_class(_swagger_client.ProcessApi)

    def _rest_api_configuration(self):
        """
        Instantiate Configuration REST API

        Returns:
            acceleratorAPI.rest_api.swagger_client.ConfigurationApi: class instance
        """
        # /v1.0/configuration/
        return self._init_rest_api_class(_swagger_client.ConfigurationApi)

    def _rest_api_stop(self):
        """
        Instantiate Stop REST API

        Returns:
            acceleratorAPI.rest_api.swagger_client.StopApi: class instance
        """
        # /v1.0/stop
        return self._init_rest_api_class(_swagger_client.StopApi)

    def stop_accelerator(self):
        return self._rest_api_stop().stop_list()


class AcceleratorClass(object):
    """
    This class automatically handle Accelerator API and CSP.

    Args:
        accelerator:
        config_file:
        provider:
        region:
        xlz_client_id:
        xlz_secret_id:
        csp_client_id:
        csp_secret_id:
        ssh_key:
        instance_id:
        instance_ip:
        exit_instance_on_signal (bool): If True, exit CSP instances
            on OS exit signals. This may help to not have instance still running
            if accelerator is not exited properly. Note: this is provided for
            convenience and does not cover all exit case like process kill and
            may not work on every OS.
    """
    def __init__(self, accelerator, config_file=None, provider=None,
                 region=None, xlz_client_id=None, xlz_secret_id=None, csp_client_id=None,
                 csp_secret_id=None, ssh_key=None, instance_id=None, instance_ip=None,
                 exit_instance_on_signal=True):
        logger.debug("")
        logger.debug("/" * 100)

        # Initialize configuration
        self._config = _create_configuration(config_file)
        logger.info("Using configuration file: %s", self._config.file_path)

        # Create CSP object
        instance_url = ("http://%s" % instance_ip) if instance_ip else None
        self._csp = _CSPClassFactory(config=self._config, provider=provider, client_id=csp_client_id,
                                     secret_id=csp_secret_id, region=region, ssh_key=ssh_key, instance_id=instance_id,
                                     instance_url=instance_url)

        # Handle CSP instance stop
        self._stop_mode = TERM
        if exit_instance_on_signal:
            self._sign_handler = _SignalHandlerAccelerator(self)
        else:
            self._sign_handler = None

        # Create Accelerator object
        self._accelerator = AcceleratorApiClass(
            accelerator, client_id=xlz_client_id, secret_id=xlz_secret_id, config=self._config)

        # Checking if credentials are valid otherwise no sense to continue
        self._accelerator.check_accelize_credential()

        # Check CSP ID if provided
        if instance_id:
            self._csp.is_instance_id_valid()
            self._accelerator.url = self._csp.get_instance_url()

        # Set CSP URL if provided
        elif instance_url:
            self._accelerator.url = instance_url

    def __del__(self):
        self.stop()

    @property
    def stop_mode(self):
        """
        Stop mode

        Returns:
            int: stop mode
        """
        return self._stop_mode

    @stop_mode.setter
    def stop_mode(self, stop_mode):
        stop_modes = {
            TERM: "TERM",
            STOP: "STOP",
            KEEP: "KEEP"}

        if stop_mode not in stop_modes:
            raise ValueError(
                "Possible values are %s" %
                ', '.join("%s: %d" % (name, value) for value, name in stop_modes.items()))

        self._stop_mode = stop_mode
        logger.info("Auto-stop mode is: %s", stop_modes[self._stop_mode])

    @property
    def csp_instance(self):
        """
        CSP instance

        Returns:
            acceleratorAPI.csp.CSPGenericClass subclass: Instance
        """
        return self._csp

    @staticmethod
    def _get_info_from_result(result):
        if 'app' not in result.keys():
            return -1, "No result returned!"
        retcode = result['app']['status']
        msg = result['app']['msg']
        return retcode, msg

    @staticmethod
    def _get_profiling_from_result(result):
        if 'app' not in result.keys():
            logger.debug("No application information found in result JSON file")
            return None
        if 'profiling' not in result['app'].keys():
            logger.debug("No profiling information found in result JSON file")
            return None
        return result['app']['profiling']

    @staticmethod
    def _get_specific_from_result(result):
        if 'app' not in result.keys():
            logger.debug("No application information found in result JSON file")
            return None
        if 'specific' not in result['app'].keys():
            logger.debug("No specific information found in result JSON file")
            return None
        return result['app']['specific']

    # Start a new instance or use a running instance
    def start_instance(self, stop_mode=None):
        try:
            logger.debug("Starting instance on '%s'", self._csp.provider)
            stop_mode = self._config.get_default("csp", "stop_mode", overwrite=stop_mode, default=TERM)

            # Updates stop mode
            if stop_mode is not None:
                self._stop_mode = stop_mode

            # Get configuration information from webservice
            accel_requirements = self._accelerator.get_accelerator_requirements(self._csp.provider)

            if not self._csp.set_accelerator_requirements(accel_requirements):
                return False
            # Start CSP instance if needed
            if self._csp.instance_url is None:
                if not self._csp.check_csp_credential():
                    return False
                if self._csp.instance_id is None:
                    if not self._csp.create_instance_csp():
                        return False
                if not self._csp.start_instance_csp():
                    return False
                self._accelerator.url = self._csp.get_instance_url()
            logger.info("Accelerator URL: %s", self._accelerator.url)
            # If possible use the last accelerator configuration (it can still be overwritten later)
            self._accelerator.use_last_configuration()
            return True
        except Exception:
            logger.exception("Exception occurred:")
            return False

    def configure_accelerator(self, datafile=None, accelerator_parameters=None, **kwargs):
        try:
            logger.debug("Configuring accelerator '%s' on instance ID %s", self._accelerator.name, self._csp.instance_id)
            if not _utils.check_url(self._accelerator.url, 10, logger=logger):
                return False, {
                    'app': {'status': -1, 'msg': "Failed to reach accelerator url: %s" % self._accelerator.url}}
            csp_env = self._csp.get_configuration_env(**kwargs)
            config_result = self._accelerator.start_accelerator(datafile=datafile,
                                                                accelerator_parameters=accelerator_parameters,
                                                                csp_env=csp_env)
            ret, msg = self._get_info_from_result(config_result)
            if ret:
                logger.error("Configuration of accelerator failed: %s", msg)
                return False, config_result
            logger.info("Configuration of accelerator is complete")
            return True, config_result
        except Exception:
            logger.exception("Exception occurred:")
            return False, {'app': {'status': -1, 'msg': "Exception occurred"}}

    def start(self, stop_mode=None, datafile=None, accelerator_parameters=None, **kwargs):
        try:
            # Start a new instance or use a running instance
            if not self.start_instance(stop_mode):
                return False, {'app': {'status': 0, 'msg': "Failed to create instance on %s" % self._csp.provider}}
            # Configure accelerator if needed
            if kwargs or (self._accelerator.configuration_url is None) or datafile is not None:
                return self.configure_accelerator(datafile, accelerator_parameters, **kwargs)
            logger.debug("Accelerator is already configured")
            return True, {'app': {'status': 0,
                                  'msg': "Reusing last configuration: %s" %
                                         self._accelerator.configuration_url}}
        except Exception:
            logger.exception("Exception occurred:")
            return False, {'app': {'status': -1, 'msg': "Exception occurred"}}

    def process(self, file_out, file_in=None, process_parameter=None):
        try:
            logger.debug("Starting a processing job: in=%s, out=%s", file_in, file_out)
            if file_in and not os.path.isfile(file_in):
                logger.error("Could not find input file: %s", file_in)
                return False, {'app': {'status': -1, 'msg': "Invalid input file path: %s" % file_in}}
            accel_url = self._accelerator.url
            logger.debug("Accelerator URL: %s", accel_url)
            if not _utils.check_url(accel_url, 10, logger=logger):
                return False, {
                    'app': {'status': -1, 'msg': "Failed to reach accelerator url: %s" % self._accelerator.url}}
            process_result = self._accelerator.process_file(file_in=file_in, file_out=file_out,
                                                            accelerator_parameters=process_parameter)
            profiling = self._get_profiling_from_result(process_result)
            if profiling is not None:
                total_bytes = 0
                global_time = 0.0
                fpga_time = 0.0
                if 'wall-clock-time' in profiling.keys():
                    global_time = float(profiling['wall-clock-time'])
                else:
                    logger.debug("No 'wall-clock-time' found in output JSON file.")
                if 'fpga-elapsed-time' in profiling.keys():
                    fpga_time = float(profiling['fpga-elapsed-time'])
                else:
                    logger.debug("No 'fpga-elapsed-time' found in output JSON file.")
                if 'total-bytes-written' in profiling.keys():
                    total_bytes += int(profiling['total-bytes-written'])
                else:
                    logger.debug("No 'total-bytes-written' found in output JSON file.")
                if 'total-bytes-read' in profiling.keys():
                    total_bytes += int(profiling['total-bytes-read'])
                else:
                    logger.debug("No 'total-bytes-read' found in output JSON file.")
                logger.info("Profiling information from result:\n%s",
                            json.dumps(profiling, indent=4).replace('\\n', '\n').replace('\\t', '\t'))
                if total_bytes > 0 and global_time > 0.0:
                    bw = total_bytes / global_time / 1024 / 1024
                    fps = 1.0 / global_time
                    logger.debug("Server processing bandwidths on %s: round-trip = %0.1f MB/s, frame rate = %0.1f fps",
                                 self._csp.provider, bw, fps)
                if total_bytes > 0 and fpga_time > 0.0:
                    bw = total_bytes / fpga_time / 1024 / 1024
                    fps = 1.0 / fpga_time
                    logger.debug("FPGA processing bandwidths on %s: round-trip = %0.1f MB/s, frame rate = %0.1f fps",
                                 self._csp.provider, bw, fps)
            specific = self._get_specific_from_result(process_result)
            if specific is not None and len(specific.keys()):
                logger.info("Specific information from result:\n%s",
                            json.dumps(specific, indent=4).replace('\\n', '\n').replace('\\t', '\t'))
            ret, msg = self._get_info_from_result(process_result)
            b_ret = False if ret else True
            return b_ret, process_result
        except Exception:
            logger.exception("Exception occurred:")
            return False, {'app': {'status': -1, 'msg': "Exception occurred"}}

    def stop_accelerator(self):
        logger.debug("Stopping accelerator '%s' on instance ID %s", self._accelerator.name, self._csp.instance_id)
        try:
            if not _utils.check_url(self._accelerator.url, 10, logger=logger):
                return False, {
                    'app': {'status': -1, 'msg': "Failed to reach accelerator url: %s" % self._accelerator.url}}
            stop_result = self._accelerator.stop_accelerator()
            ret, msg = self._get_info_from_result(stop_result)
            if ret:
                logger.error("Stopping accelerator failed: %s", msg)
                return False, stop_result
            logger.info("Accelerator session is closed")
            return True, stop_result
        except Exception:
            logger.exception("Exception occurred:")
            return False, {'app': {'status': -1, 'msg': "Exception occurred"}}

    def stop_instance(self, terminate=True):
        logger.debug("Stopping instance (ID: %s) on '%s'", self._csp.instance_id, self._csp.provider)
        try:
            res = self.stop_accelerator()
            self._csp.stop_instance_csp(terminate)

            return res
        except Exception:
            logger.exception("Exception occurred:")
            return False, {'app': {'status': -1, 'msg': "Exception occurred"}}

    def stop(self, stop_mode=None):
        try:
            if stop_mode is None:
                stop_mode = self.stop_mode
            if stop_mode == KEEP:
                return self.stop_accelerator()
            terminate = True if stop_mode == TERM else False
            return self.stop_instance(terminate)
        except Exception:
            logger.exception("Exception occurred:")
            return False, {'app': {'status': -1, 'msg': "Exception occurred"}}
