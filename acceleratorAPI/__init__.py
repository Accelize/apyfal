# coding=utf-8
__version__ = "2.0.3"

import ast
import json
import os
import shutil
import signal
import socket

try:
    # Python 3
    from configparser import ConfigParser
except ImportError:
    # Python 2
    from ConfigParser import ConfigParser

import requests
from requests.adapters import HTTPAdapter

import rest_api.swagger_client
from rest_api.swagger_client.rest import ApiException

from acceleratorAPI.utilities import init_logger, check_url, pretty_dict

# Initialize logger
logger = init_logger(__name__, __file__)

from acceleratorAPI.csp import CSPClassFactory

DEFAULT_CONFIG_FILE = "accelerator.conf"
SOCKET_TIMEOUT = 1200

TERM = 0
STOP = 1
KEEP = 2


class _SignalHandlerAccelerator(object):

    '''Signal handler for Instances'''
    STOPMODE = {TERM: "TERM",
                STOP: "STOP",
                KEEP: "KEEP"}

    def __init__(self):
        self.csp = None
        self.stop_mode = TERM
        self.set_signals()
        self.defaultSocketTimeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(SOCKET_TIMEOUT)

    def add_instance(self, instance):
        self.csp = instance
        logger.debug("Added instance to auto-stop handler.")

    def remove_instance(self):
        if self.csp is None:
            logger.debug("There is no registered instance to stop")
            return
        logger.debug("Removed instance with URL %s (ID=%s) from auto-stop handler.", self.csp.instance_url,
                     self.csp.instance_id)
        self.csp = None

    def set_stop_mode(self, stop_mode):
        self.stop_mode = int(stop_mode)
        logger.info("Auto-stop mode is: %s", self.STOPMODE[self.stop_mode])

    def set_signals(self):
        '''Set a list of interrupt signals to be handled asynchronously'''
        for signal_name in ('SIGTERM', 'SIGINT', 'SIGQUIT'):
            # Check signal exist on current OS before setting it
            if hasattr(signal, signal_name):
                signal.signal(getattr(signal, signal_name), self.signal_handler_accelerator)

    def signal_handler_accelerator(self, _signo="", _stack_frame="", exit=True):
        '''Try to stop all instances running or inform user'''
        try:
            if self.csp is None:
                logger.debug("There is no registered instance to stop")
                return
            if self.stop_mode == KEEP or not self.csp.get_instance_csp():
                logger.warn("###########################################################")
                logger.warn("## Instance with URL %s (ID=%s) is still running!", self.csp.instance_url,
                            self.csp.instance_id)
                logger.warn("## Make sure you will stop manually the instance.")
                logger.warn("###########################################################")
            else:
                terminate = True if self.stop_mode == TERM else False
                self.csp.stop_instance_csp(terminate)
        finally:
            logger.info("More detailed messages can be found in %s", logger.filename)
            if exit:
                socket.setdefaulttimeout(self.defaultSocketTimeout)
                logger.info("Accelerator API Closed properly")
                os._exit(0)


class _GenericAcceleratorClass(object):
    '''
    EndUser API based on the openAPI Accelize accelerator
    Objective of this API it to remove complex user actions
    '''

    def __init__(self, accelerator, client_id, secret_id, url=None):
        # A regular API has fixed url. In our case we want to change it dynamically.
        self.name = accelerator
        self.api_configuration = rest_api.swagger_client.Configuration()
        self.api_configuration.host = url
        self.accelerator_configuration_url = None
        self.client_id = client_id
        self.secret_id = secret_id

    def check_accelize_credential(self):
        try:
            s = requests.Session()
            s.mount('https://', HTTPAdapter(max_retries=2))
            r = s.post('https://master.metering.accelize.com/o/token/', data={"grant_type": "client_credentials"},
                       auth=(self.client_id, self.secret_id))
            if r.status_code != 200:
                logger.error("Accelize authentication failed (%d): %s", r.status_code, r.text)
                return False
            logger.info("Accelize authentication for '%s' is successful", self.name)
            return True
        except Exception:
            logger.exception("Caught following exception:")
            return False

    def set_url(self, url):
        self.api_configuration.host = url

    def get_url(self):
        return self.api_configuration.host

    def get_accelerator_requirements(self, provider):
        try:
            s = requests.Session()
            s.mount('https://', HTTPAdapter(max_retries=2))
            r = s.post('https://master.metering.accelize.com/o/token/', data={"grant_type": "client_credentials"},
                       auth=(self.client_id, self.secret_id))
            logger.debug("Accelize token answer: %s", str(r.text))
            r.raise_for_status()
            if r.status_code == 200:
                # call WS
                answer_token = json.loads(r.text)
                headers = {"Authorization": "Bearer " + str(answer_token['access_token']),
                           "Content-Type": "application/json", "Accept": "application/vnd.accelize.v1+json"}
                r = s.get('https://master.metering.accelize.com/auth/getlastcspconfiguration/', headers=headers)
                logger.debug("Accelize config answer: %s, status: %s", r.text, str(r.status_code))
                r.raise_for_status()
                configuration_accelerator = json.loads(r.text)
                logger.debug("Accelerator requirements:\n%s", pretty_dict(configuration_accelerator))
                if provider not in configuration_accelerator.keys():
                    logger.error("CSP '%s' is not supported. Available CSP are: %s", provider,
                                 ', '.join(configuration_accelerator.keys()))
                    return None
                if self.name not in configuration_accelerator[provider].keys():
                    logger.error("Accelerator '%s' is not supported on '%s'.", self.name, provider)
                    return None
                info = configuration_accelerator[provider][self.name]
                info['accelerator'] = self.name
                return info
        except Exception:
            logger.exception("Caught following exception:")
            return None

    def get_accelerator_configuration_list(self):
        try:
            # /v1.0/configuration/
            # create an instance of the API class
            if self.api_configuration.host is None:
                logger.error("An accelerator url is required to get the list of configurations.")
                return None
            api_instance = rest_api.swagger_client.ConfigurationApi(api_client=self.api_configuration.api_client)
            api_instance.api_client.rest_client.pool_manager.connection_pool_kw['retries'] = 3
            logger.debug("Get list of configurations...")
            api_response = api_instance.configuration_list()
            config_list = api_response.results
            # logger.debug("configuration_list api_response:\n%s", pretty_dict(api_response))
            # if api_response.inerror :
            #    raise ValueError("Cannot get list of configurations")
            #    return None
            return config_list
        except ApiException:
            logger.exception("Caught following exception while calling ConfigurationApi->configuration_list:")
            return None
        except Exception:
            logger.exception("Caught following exception:")
            return None

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
        self.accelerator_configuration_url = last_config.url
        return True

    # Create an Accelerator configuration
    def start_accelerator(self, datafile=None, accelerator_parameters=None, csp_env=None):
        try:
            # /v1.0/configuration/
            # create an instance of the API class
            api_instance = rest_api.swagger_client.ConfigurationApi(api_client=self.api_configuration.api_client)
            api_instance.api_client.rest_client.pool_manager.connection_pool_kw['retries'] = 3
            if accelerator_parameters is None:
                logger.debug("Using default configuration parameters")
                accelerator_parameters = ast.literal_eval(config.get("configuration", "parameters"))
            envserver = {"client_id": self.client_id, "client_secret": self.secret_id}
            envserver.update(csp_env)
            parameters = {"env": envserver}
            parameters.update(accelerator_parameters)
            logger.debug("parameters = \n%s", json.dumps(parameters, indent=4))
            logger.debug("datafile = %s", datafile)
            logger.info("Configuring accelerator...")
            if datafile is None:
                datafile = ""
            api_response = api_instance.configuration_create(parameters=json.dumps(parameters), datafile=datafile)
            logger.debug("configuration_create api_response:\n%s", str(api_response))
            api_resp_id = api_response.id
            self.accelerator_configuration_url = api_response.url
            dictparameters = ast.literal_eval(api_response.parametersresult)
            dictparameters['url_config'] = api_response.url
            dictparameters['url_instance'] = self.api_configuration.host
            logger.debug("status: %s", str(dictparameters['app']['status']))
            logger.debug("msg:\n%s", dictparameters['app']['msg'])
            api_response_read = api_instance.configuration_read(api_resp_id)
            if api_response_read.inerror:
                return {'app': {'status': -1, 'msg': "Cannot start the configuration %s" % api_response_read.url}}
            return dictparameters
        except ApiException as e:
            logger.exception("Caught following exception while calling ConfigurationApi->configuration_create:")
            return {'app': {'status': -1, 'msg': str(e)}}
        except Exception:
            logger.exception("Caught following exception:")
            return {'app': {'status': -1, 'msg': "Caught exception"}}

    def process_file(self, file_in, file_out, accelerator_parameters=None):
        if self.accelerator_configuration_url is None:
            logger.error("Accelerator has not been configured. Use 'start_accelerator' function.")
            return {'app': {'status': -1, 'msg': "Accelerator is not configured."}}
        # create an instance of the API class
        api_instance = rest_api.swagger_client.ProcessApi(api_client=self.api_configuration.api_client)
        api_instance.api_client.rest_client.pool_manager.connection_pool_kw['retries'] = 3
        if accelerator_parameters is None:
            logger.debug("Using default processing parameters")
            accelerator_parameters = ast.literal_eval(config.get("process", "parameters"))
        logger.debug("Using configuration: %s", self.accelerator_configuration_url)
        datafile = file_in  # file | If needed, file to be processed by the accelerator. (optional)
        try:
            try:  # Bypass REST API because upload issue with big file using python https://bugs.python.org/issue8450
                import pycurl
            except ImportError:
                logger.debug("process_create process=%s datafile=%s", self.accelerator_configuration_url, str(datafile))
                api_response = api_instance.process_create(self.accelerator_configuration_url,
                                                           parameters=json.dumps(accelerator_parameters),
                                                           datafile=datafile)
                api_resp_id = api_response.id
                processed = api_response.processed
            else:
                try:
                    # Python 2
                    from StringIO import StringIO
                except ImportError:
                    # Python 3
                    from io import StringIO
                logger.debug("pycurl process=%s datafile=%s", self.accelerator_configuration_url, str(datafile))
                retries_max = 3
                retries_done = 1
                while True:
                    try:
                        storage = StringIO()
                        c = pycurl.Curl()
                        c.setopt(c.WRITEFUNCTION, storage.write)
                        c.setopt(c.URL, self.api_configuration.host + "/v1.0/process/")
                        c.setopt(c.POST, 1)
                        post = [("parameters", json.dumps(accelerator_parameters)),
                                ("configuration", self.accelerator_configuration_url)]
                        if file_in is not None:
                            post.append(("datafile", (c.FORM_FILE, file_in)))
                        c.setopt(c.HTTPPOST, post)
                        c.setopt(c.HTTPHEADER, ['Content-Type: multipart/form-data'])
                        # c.setopt(c.VERBOSE, 1)
                        c.perform()
                        break
                    except Exception as e:
                        logger.error("Failed to post process request after %d/%d attempts because of: %s", retries_done,
                                     retries_max, str(e))
                        if retries_done > retries_max:
                            raise e
                        retries_done += 1
                    finally:
                        c.close()
                content = storage.getvalue()
                logger.debug("pycurl process:" + str(content))
                r2 = json.loads(content)
                if 'id' not in r2.keys():
                    msg = "Processing failed with no message (host application did not run)."
                    logger.error(msg)
                    return {'app': {'status': -1, 'msg': msg}}
                api_resp_id = r2['id']
                processed = r2['processed']
            try:
                while processed is not True:
                    api_response = api_instance.process_read(api_resp_id)
                    processed = api_response.processed
                dictparameters = ast.literal_eval(api_response.parametersresult)
                if api_response.inerror:
                    msg = "Failed to process data: %s" % pretty_dict(api_response.parametersresult)
                    logger.error(msg)
                    return {'app': {'status': -1, 'msg': msg}}
                logger.debug("Process status: %s", str(dictparameters['app']['status']))
                logger.debug("Process msg:\n%s", str(dictparameters['app']['msg']))
                s = requests.Session()
                s.mount('https://', HTTPAdapter(max_retries=2))
                response = s.get(api_response.datafileresult, stream=True)
                with open(file_out, 'wb') as out_file:
                    shutil.copyfileobj(response.raw, out_file)
            finally:
                logger.debug("process_delete api_response: " + str(api_resp_id))
                api_instance.process_delete(api_resp_id)
            return dictparameters
        except ApiException as e:
            logger.error("Caught following exception while calling ProcessApi->process_create: %s", str(e))
            return {'app': {'status': -1, 'msg': str(e)}}
        except Exception:
            logger.exception("Caught following exception:")
            return {'app': {'status': -1, 'msg': "Caught exception"}}

    def stop_accelerator(self):
        # create an instance of the API class
        api_instance = rest_api.swagger_client.StopApi(api_client=self.api_configuration.api_client)
        api_instance.api_client.rest_client.pool_manager.connection_pool_kw['retries'] = 3
        try:
            # /v1.0/stop
            return api_instance.stop_list()
        except ApiException as e:
            logger.exception("Caught following exception while calling StopApi->stop_list:")
            return {'app': {'status': -1, 'msg': str(e)}}
        except Exception as e:
            logger.exception("Caught following exception:")
            return {'app': {'status': -1, 'msg': str(e)}}


class AcceleratorClass(object):
    '''
    This Class is hiding complexity of using GenericAcceleratorClass and CSPGenericClass
    '''

    def __init__(self, accelerator, config_file=None, provider=None,
                 region=None, xlz_client_id=None, xlz_secret_id=None, csp_client_id=None,
                 csp_secret_id=None, ssh_key=None, instance_id=None, instance_ip=None):
        global config
        logger.debug("")
        logger.debug("/" * 100)
        if config_file is None:
            config_file = DEFAULT_CONFIG_FILE
        if not os.path.isfile(config_file):
            raise Exception("Could not find configuration file: %s" % config_file)
        logger.info("Using configuration file: %s", config_file)
        if instance_ip:
            instance_url = "http://" + instance_ip
        else:
            instance_url = None
        # Create CSP object
        self.sign_handler = _SignalHandlerAccelerator()
        self.csp = CSPClassFactory(config_file=config_file, provider=provider, client_id=csp_client_id,
                                   secret_id=csp_secret_id, region=region, ssh_key=ssh_key, instance_id=instance_id,
                                   instance_url=instance_url)
        # Create Accelerator object
        config = ConfigParser(allow_no_value=True)
        config.read(config_file)
        if xlz_client_id is None:
            try:
                xlz_client_id = config.get('accelize', 'client_id')
            except Exception:
                raise Exception(
                    "Accelize client ID and secret ID are mandatory. "
                    "Provide them in the configuration file or through function arguments.")
        if xlz_secret_id is None:
            try:
                xlz_secret_id = config.get('accelize', 'secret_id')
            except Exception:
                raise Exception(
                    "Accelize client ID and secret ID are mandatory. "
                    "Provide them in the configuration file or through function arguments.")
        self.accelerator = _GenericAcceleratorClass(accelerator, client_id=xlz_client_id, secret_id=xlz_secret_id)
        # Checking if credentials are valid otherwise no sense to continue
        if not self.accelerator.check_accelize_credential():
            raise Exception("Could not authenticate to your Accelize account")
        # Check CSP ID if provided
        if instance_id:
            if not self.csp.is_instance_ID_valid():
                raise Exception("Could not find instance with ID: %s" % instance_id)
            self.accelerator.set_url(self.csp.get_instance_url())
        # Set CSP URL if provided
        if instance_url:
            self.accelerator.set_url(instance_url)

    def __del__(self):
        self.sign_handler.signal_handler_accelerator(exit=False)

    @staticmethod
    def get_info_from_result(result):
        if 'app' not in result.keys():
            return -1, "No result returned!"
        retcode = result['app']['status']
        msg = result['app']['msg']
        return retcode, msg

    @staticmethod
    def get_profiling_from_result(result):
        if 'app' not in result.keys():
            logger.debug("No application information found in result JSON file")
            return None
        if 'profiling' not in result['app'].keys():
            logger.debug("No profiling information found in result JSON file")
            return None
        return result['app']['profiling']

    @staticmethod
    def get_specific_from_result(result):
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
            logger.debug("Starting instance on '%s'", self.csp.provider)
            stop_mode = self.csp.get_from_config("csp", "stop_mode", overwrite=stop_mode, default=TERM)
            if stop_mode is not None:
                self.sign_handler.set_stop_mode(stop_mode)
            self.sign_handler.add_instance(self.csp)
            # Get configuration information from webservice
            accel_requirements = self.accelerator.get_accelerator_requirements(self.csp.provider)
            if accel_requirements is None:
                return False
            if not self.csp.set_accelerator_requirements(accel_requirements):
                return False
            # Start CSP instance if needed
            if self.csp.instance_url is None:
                if not self.csp.check_csp_credential():
                    return False
                if self.csp.instance_id is None:
                    if not self.csp.create_instance_csp():
                        return False
                if not self.csp.start_instance_csp():
                    return False
                self.accelerator.set_url(self.csp.get_instance_url())
            logger.info("Accelerator URL: %s", self.accelerator.get_url())
            # If possible use the last accelerator configuration (it can still be overwritten later)
            self.accelerator.use_last_configuration()
            return True
        except Exception:
            logger.exception("Exception occurred:")
            return False

    def configure_accelerator(self, datafile=None, accelerator_parameters=None, **kwargs):
        try:
            logger.debug("Configuring accelerator '%s' on instance ID %s", self.accelerator.name, self.csp.instance_id)
            if not check_url(self.accelerator.get_url(), 10, logger=logger):
                return False, {
                    'app': {'status': -1, 'msg': "Failed to reach accelerator url: %s" % self.accelerator.get_url()}}
            csp_env = self.csp.get_configuration_env(**kwargs)
            config_result = self.accelerator.start_accelerator(datafile=datafile,
                                                               accelerator_parameters=accelerator_parameters,
                                                               csp_env=csp_env)
            ret, msg = self.get_info_from_result(config_result)
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
                return False, {'app': {'status': 0, 'msg': "Failed to create instance on %s" % self.csp.provider}}
            # Configure accelerator if needed
            if kwargs or (self.accelerator.accelerator_configuration_url is None) or datafile is not None:
                return self.configure_accelerator(datafile, accelerator_parameters, **kwargs)
            logger.debug("Accelerator is already configured")
            return True, {'app': {'status': 0,
                                  'msg': "Reusing last configuration: %s" %
                                         self.accelerator.accelerator_configuration_url}}
        except Exception:
            logger.exception("Exception occurred:")
            return False, {'app': {'status': -1, 'msg': "Exception occurred"}}

    def process(self, file_out, file_in=None, process_parameter=None):
        try:
            logger.debug("Starting a processing job: in=%s, out=%s", file_in, file_out)
            if file_in and not os.path.isfile(file_in):
                logger.error("Could not find input file: %s", file_in)
                return False, {'app': {'status': -1, 'msg': "Invalid input file path: %s" % file_in}}
            accel_url = self.accelerator.get_url()
            logger.debug("Accelerator URL: %s", accel_url)
            if not check_url(accel_url, 10, logger=logger):
                return False, {
                    'app': {'status': -1, 'msg': "Failed to reach accelerator url: %s" % self.accelerator.get_url()}}
            process_result = self.accelerator.process_file(file_in=file_in, file_out=file_out,
                                                           accelerator_parameters=process_parameter)
            profiling = self.get_profiling_from_result(process_result)
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
                                 self.csp.provider, bw, fps)
                if total_bytes > 0 and fpga_time > 0.0:
                    bw = total_bytes / fpga_time / 1024 / 1024
                    fps = 1.0 / fpga_time
                    logger.debug("FPGA processing bandwidths on %s: round-trip = %0.1f MB/s, frame rate = %0.1f fps",
                                 self.csp.provider, bw, fps)
            specific = self.get_specific_from_result(process_result)
            if specific is not None and len(specific.keys()):
                logger.info("Specific information from result:\n%s",
                            json.dumps(specific, indent=4).replace('\\n', '\n').replace('\\t', '\t'))
            ret, msg = self.get_info_from_result(process_result)
            b_ret = False if ret else True
            return b_ret, process_result
        except Exception:
            logger.exception("Exception occurred:")
            return False, {'app': {'status': -1, 'msg': "Exception occurred"}}

    def stop_accelerator(self):
        logger.debug("Stopping accelerator '%s' on instance ID %s", self.accelerator.name, self.csp.instance_id)
        try:
            if not check_url(self.accelerator.get_url(), 10, logger=logger):
                return False, {
                    'app': {'status': -1, 'msg': "Failed to reach accelerator url: %s" % self.accelerator.get_url()}}
            stop_result = self.accelerator.stop_accelerator()
            ret, msg = self.get_info_from_result(stop_result)
            if ret:
                logger.error("Stopping accelerator failed: %s", msg)
                return False, stop_result
            logger.info("Accelerator session is closed")
            return True, stop_result
        except Exception:
            logger.exception("Exception occurred:")
            return False, {'app': {'status': -1, 'msg': "Exception occurred"}}

    def stop_instance(self, terminate=True):
        logger.debug("Stopping instance (ID: %s) on '%s'", self.csp.instance_id, self.csp.provider)
        try:
            res = self.stop_accelerator()
            self.csp.stop_instance_csp(terminate)
            self.sign_handler.remove_instance()
            return res
        except Exception:
            logger.exception("Exception occurred:")
            return False, {'app': {'status': -1, 'msg': "Exception occurred"}}

    def stop(self, stop_mode=None):
        try:
            if stop_mode is None:
                stop_mode = self.sign_handler.stop_mode
            if stop_mode == KEEP:
                return self.stop_accelerator()
            terminate = True if stop_mode == TERM else False
            return self.stop_instance(terminate)
        except Exception:
            logger.exception("Exception occurred:")
            return False, {'app': {'status': -1, 'msg': "Exception occurred"}}
