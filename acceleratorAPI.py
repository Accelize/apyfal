__version__ = "2.0.3"

import os
import sys
import inspect
import logging
import logging.handlers
import time
import signal
import shutil
import copy
import ast
import json
import requests
import socket
import ConfigParser

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

import rest_api.swagger_client
from rest_api.swagger_client.rest import ApiException


#===================================
# Custom logger that:
# - Forwards records to parent logger if not an exception (but save it into the log file)
# - Force the level to DEBUG for the file handler.
class APILogger(logging.getLoggerClass()):
#===================================
    LevelRequest = logging.WARN
    def setLevel(self, lvl):
        self.LevelRequest = lvl
        if self.name != __name__:
            super(APILogger, self).setLevel(lvl)
        else:
            super(APILogger, self).setLevel(logging.DEBUG)
    def handle(self, record):
        for e in self.handlers:
            e.emit(record)
        if record.name == __name__ and record.levelno < self.LevelRequest:
            return
        if record.name == __name__ and record.exc_info is not None:
            record.msg = record.exc_info[1].message
            record.exc_text = None
            record.exc_info = None
        self.parent.handle(record)


# Register our logger class and create local logger object
refLoggerClass = logging.getLoggerClass()
logging.setLoggerClass(APILogger)
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARN)
# Use the original Logger class for the others
logging.setLoggerClass(refLoggerClass)

# Rotating file handler
LOG_FILENAME = os.path.splitext(os.path.basename(__file__))[0] + ".log"
MAX_BYTES = 100*1024*1024
fileHandler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=MAX_BYTES, backupCount=5)
fileHandler.setLevel(logging.DEBUG)
fileHandler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)-8s: %(module)-20s, %(funcName)-28s, %(lineno)-4d: %(message)s"))
logger.addHandler(fileHandler)

DEFAULT_CONFIG_FILE = "accelerator.conf"
SOCKET_TIMEOUT = 1200

TERM = 0
STOP = 1
KEEP = 2


def check_url(url, timeout=None, retryCount=0, retryPeriod=5):
    '''
        Checking if an HTTP is up and running.
    '''
    if not url:
        logger.error("Invalid url: %s", str(url))
        return False
    t = socket.getdefaulttimeout()
    missCnt = 0
    try:
        if timeout is not None:
            socket.setdefaulttimeout( timeout )  # timeout in seconds
        while missCnt <= retryCount:
            try :
                logger.debug("Check URL server: %s...", url)
                status_code = requests.get(url).status_code
                if status_code == 200:
                    logger.debug("... hit!")
                    return True
            except Exception as e:
                logger.debug("... miss")
                missCnt += 1
                time.sleep(retryPeriod)
        logger.error("Cannot reach url '%s' after %d attempts", url, retryCount)
        return False
    finally:
        socket.setdefaulttimeout( t )  # set back to default value


def pretty_dict(obj):
    return json.dumps(ast.literal_eval(str(obj)), indent=4)


#===================================
class SignalHandlerAccelerator(object):
#===================================
    '''Signal handler for Instances'''
    STOPMODE = { TERM: "TERM",
                 STOP: "STOP",
                 KEEP: "KEEP" }

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
        logger.debug("Removed instance with URL %s (ID=%s) from auto-stop handler.", self.csp.instance_url, self.csp.instance_id)
        self.csp = None

    def set_stop_mode(self, stop_mode):
        self.stop_mode = int(stop_mode)
        logger.info("Auto-stop mode is: %s", self.STOPMODE[self.stop_mode])

    def set_signals(self):
        '''Set a list of interrupt signals to be handled asynchronously'''
        signal.signal(signal.SIGTERM, self.signal_handler_accelerator)
        signal.signal(signal.SIGINT, self.signal_handler_accelerator)
        signal.signal(signal.SIGQUIT, self.signal_handler_accelerator)

    def signal_handler_accelerator(self, _signo="", _stack_frame="", exit=True):
        '''Try to stop all instances running or inform user'''
        try:
            if self.csp is None:
                logger.debug("There is no registered instance to stop")
                return
            if self.stop_mode == KEEP or not self.csp.get_instance_csp():
                logger.warn("###########################################################")
                logger.warn("## Instance with URL %s (ID=%s) is still running!", self.csp.instance_url, self.csp.instance_id)
                logger.warn("## Make sure you will stop manually the instance.")
                logger.warn("###########################################################")
            else:
                terminate = True if self.stop_mode == TERM else False
                self.csp.stop_instance_csp(terminate)
        finally:
            logger.info("More detailed messages can be found in %s", fileHandler.baseFilename)
            if exit:
                socket.setdefaulttimeout(self.defaultSocketTimeout)
                logger.info("Accelerator API Closed properly")
                os._exit(0)

################################# Rest API material [begin] ########################################################

#===================================
class GenericAcceleratorClass(object):
#===================================
    '''############################################################
    #####  EndUser API based on the openAPI Accelize accelerator
    #####  Objective of this API it to remove complex user actions
    ###############################################################
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
        try :
            s = requests.Session()
            s.mount('https://', HTTPAdapter(max_retries=2))
            r = s.post('https://master.metering.accelize.com/o/token/',data={"grant_type":"client_credentials"} , auth=(self.client_id, self.secret_id))
            if r.status_code != 200 :
                logger.error("Accelize authentication failed (%d): %s", r.status_code, r.text)
                return False
            logger.info("Accelize authentication for '%s' is successful", self.name)
            return True
        except:
            logger.exception("Caught following exception:")
            return False

    def set_url(self, url):
        self.api_configuration.host = url

    def get_url(self):
        return self.api_configuration.host

    def get_accelerator_requirements(self, provider):
        try :
            s = requests.Session()
            s.mount('https://', HTTPAdapter(max_retries=2))
            r = s.post('https://master.metering.accelize.com/o/token/',data={"grant_type":"client_credentials"} , auth=(self.client_id, self.secret_id))
            logger.debug( "Accelize token answer: %s", str(r.text))
            r.raise_for_status()
            if r.status_code == 200 :
                #call WS
                answer_token = json.loads(r.text)
                headers = {"Authorization": "Bearer "+str(answer_token['access_token']),"Content-Type":"application/json","Accept":"application/vnd.accelize.v1+json"}
                r = s.get('https://master.metering.accelize.com/auth/getlastcspconfiguration/',headers=headers)
                logger.debug( "Accelize config answer: %s, status: %s", r.text , str(r.status_code))
                r.raise_for_status()
                configuration_accelerator = json.loads(r.text)
                logger.debug("Accelerator requirements:\n%s", pretty_dict(configuration_accelerator))
                if provider not in configuration_accelerator.keys():
                    logger.error("CSP '%s' is not supported. Available CSP are: %s", provider, ', '.join(configuration_accelerator.keys()))
                    return None
                if self.name not in configuration_accelerator[provider].keys():
                    logger.error("Accelerator '%s' is not supported on '%s'.", self.name, provider)
                    return None
                info = configuration_accelerator[provider][self.name]
                info['accelerator'] = self.name
                return info
        except:
            logger.exception("Caught following exception:")
            return None

    def get_accelerator_configuration_list(self) :
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
            configList = api_response.results
            #logger.debug("configuration_list api_response:\n%s", pretty_dict(api_response))
            #if api_response.inerror :
            #    raise ValueError("Cannot get list of configurations")
            #    return None
            return configList
        except ApiException:
            logger.exception("Caught following exception while calling ConfigurationApi->configuration_list:")
            return None
        except:
            logger.exception("Caught following exception:")
            return None

    def use_last_configuration(self):
        # Get last configuration, if any
        configList = self.get_accelerator_configuration_list()
        if not configList:
            logger.info("Accelerator has not been configured yet.")
            return False
        last_config = configList[0]
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
                logger.debug( "Using default configuration parameters")
                accelerator_parameters = ast.literal_eval(config.get("configuration", "parameters"))
            envserver = { "client_id":self.client_id, "client_secret":self.secret_id }
            envserver.update(csp_env)
            parameters = {"env":envserver}
            parameters.update(accelerator_parameters)
            logger.debug("parameters = \n%s", json.dumps(parameters, indent=4))
            logger.debug("datafile = %s", datafile)
            logger.info("Configuring accelerator...")
            if datafile is None:
                datafile = ""
            api_response = api_instance.configuration_create(parameters=json.dumps(parameters), datafile=datafile)
            logger.debug("configuration_create api_response:\n%s", str(api_response))
            id = api_response.id
            self.accelerator_configuration_url = api_response.url
            dictparameters = ast.literal_eval(api_response.parametersresult)
            dictparameters['url_config'] = api_response.url
            dictparameters['url_instance'] = self.api_configuration.host
            logger.debug("status: %s", str(dictparameters['app']['status']))
            logger.debug("msg:\n%s", dictparameters['app']['msg'])
            api_response_read = api_instance.configuration_read(id)
            if api_response_read.inerror:
                return {'app': {'status':-1, 'msg':"Cannot start the configuration %s" % api_response_read.url}}
            return dictparameters
        except ApiException as e:
            logger.exception("Caught following exception while calling ConfigurationApi->configuration_create:")
            return {'app': {'status':-1, 'msg':str(e)}}
        except:
            logger.exception("Caught following exception:")
            return {'app': {'status':-1, 'msg':"Caught exception"}}

    def process_file(self, file_in, file_out, accelerator_parameters=None):
        if self.accelerator_configuration_url is None:
            logger.error("Accelerator has not been configured. Use 'start_accelerator' function.")
            return {'app': {'status':-1, 'msg':"Accelerator is not configured."}}
        # create an instance of the API class
        api_instance = rest_api.swagger_client.ProcessApi(api_client=self.api_configuration.api_client)
        api_instance.api_client.rest_client.pool_manager.connection_pool_kw['retries'] = 3
        if accelerator_parameters == None:
            logger.debug( "Using default processing parameters")
            accelerator_parameters = ast.literal_eval(config.get("process", "parameters"))
        logger.debug("Using configuration: %s", self.accelerator_configuration_url)
        datafile = file_in # file | If needed, file to be processed by the accelerator. (optional)
        try:
            try: # Bypass REST API because upload issue with big file using python https://bugs.python.org/issue8450
                import pycurl
                from StringIO import StringIO
                logger.debug( "pycurl process=%s datafile=%s", self.accelerator_configuration_url, str(datafile) )
                retries_max = 3
                retries_done = 1
                while True:
                    try:
                        storage = StringIO()
                        c = pycurl.Curl()
                        c.setopt(c.WRITEFUNCTION, storage.write)
                        c.setopt(c.URL, self.api_configuration.host+"/v1.0/process/")
                        c.setopt(c.POST, 1)
                        c.setopt(c.HTTPPOST, [("datafile", (c.FORM_FILE, file_in)),
                                              ("parameters", json.dumps(accelerator_parameters)),
                                              ("configuration", self.accelerator_configuration_url)])
                        c.setopt(c.HTTPHEADER, ['Content-Type: multipart/form-data'])
                        #c.setopt(c.VERBOSE, 1)
                        c.perform()
                        break
                    except Exception as e:
                        logger.error("Failed to post process request after %d/%d attempts because of: %s", retries_done, retries_max, str(e))
                        if retries_done > retries_max:
                            raise e
                        retries_done += 1
                    finally:
                        c.close()
                content = storage.getvalue()
                logger.debug( "pycurl process:"+str(content) )
                r2 = json.loads(content)
                if 'id' not in r2.keys():
                    msg = "Processing failed with no message (host application did not run)."
                    logger.error(msg)
                    return {'app': {'status':-1, 'msg':msg}}
                id = r2['id']
                processed = r2['processed']
            except ImportError:
                logger.debug( "process_create process=%s datafile=%s", self.accelerator_configuration_url, str(datafile) )
                api_response = api_instance.process_create(self.accelerator_configuration_url, parameters=json.dumps(accelerator_parameters), datafile=datafile)
                id = api_response.id
                processed = api_response.processed
            try:
                while processed != True:
                    api_response = api_instance.process_read(id)
                    processed = api_response.processed
                dictparameters = ast.literal_eval(api_response.parametersresult)
                if api_response.inerror:
                    msg = "Failed to process data: %s" % pretty_dict(api_response.parametersresult)
                    logger.error(msg)
                    return {'app': {'status':-1, 'msg':msg}}
                logger.debug("Process status: %s", str(dictparameters['app']['status']))
                logger.debug("Process msg:\n%s", str(dictparameters['app']['msg']))
                url = 'http://example.com/img.png'
                s = requests.Session()
                s.mount('https://', HTTPAdapter(max_retries=2))
                response = s.get(api_response.datafileresult, stream=True)
                with open(file_out, 'wb') as out_file:
                    shutil.copyfileobj(response.raw, out_file)
            finally:
                logger.debug( "process_delete api_response: "+str(id) )
                api_response_delete = api_instance.process_delete(id)
            return dictparameters
        except ApiException as e:
            logger.error("Caught following exception while calling ProcessApi->process_create: %s", str(e))
            return {'app': {'status':-1, 'msg':str(e)}}
        except:
            logger.exception("Caught following exception:")
            return {'app': {'status':-1, 'msg':"Caught exception"}}

    def stop_accelerator(self):
        # create an instance of the API class
        api_instance = rest_api.swagger_client.StopApi(api_client=self.api_configuration.api_client)
        api_instance.api_client.rest_client.pool_manager.connection_pool_kw['retries'] = 3
        try:
            # /v1.0/stop
            return api_instance.stop_list()
        except ApiException as e:
            logger.exception("Caught following exception while calling StopApi->stop_list:")
            return {'app': {'status':-1, 'msg':str(e)}}
        except Exception as e:
            logger.exception("Caught following exception:")
            return {'app': {'status':-1, 'msg':str(e)}}

################################# Rest API material [end] ########################################################


################################# CSP material [begin] ########################################################

#===================================
class CSPGenericClass(object):
#===================================
    @staticmethod
    def get_from_args(key, **kwargs):
        try:
            return kwargs.pop(key)
        except:
            return None

    @staticmethod
    def get_host_public_ip_case1():
        try :
            url = 'http://ipinfo.io/ip'
            logger.debug("Get public IP answer using: %s", url)
            s = requests.Session()
            s.mount(url, HTTPAdapter(max_retries=1))
            r = s.get(url)
            r.raise_for_status()
            ip_address = str(r.text)
            logger.debug("Public IP answer: %s", ip_address)
            return ip_address.strip()+"/32"
        except:
            logger.exception("Caught following exception:")
            return None

    @staticmethod
    def get_host_public_ip_case2():
        try :
            import xml.etree.ElementTree as ET
            url = 'http://ip-api.com/xml'
            logger.debug("Get public IP answer using: %s", url)
            s = requests.Session()
            s.mount(url, HTTPAdapter(max_retries=1))
            r = s.get(url)
            r.raise_for_status()
            root = ET.fromstring(r.text.encode('utf-8'))
            ip_address = str(root.findall("query")[0].text)
            logger.debug("Public IP answer: %s", ip_address)
            return ip_address.strip()+"/32"
        except:
            logger.exception("Caught following exception:")
            return None

    @staticmethod
    def get_host_public_ip_case3():
        try :
            import xml.etree.ElementTree as ET
            url = 'http://freegeoip.net/xml'
            logger.debug("Get public IP answer using: %s", url)
            s = requests.Session()
            s.mount(url, HTTPAdapter(max_retries=1))
            r = s.get(url)
            r.raise_for_status()
            root = ET.fromstring(r.text.encode('utf-8'))
            ip_address = str(root.findall("IP")[0].text)
            logger.debug("Public IP answer: %s", ip_address)
            return ip_address.strip()+"/32"
        except:
            logger.exception("Caught following exception:")
            return None

    @staticmethod
    def get_host_public_ip():
        ip_address = CSPGenericClass.get_host_public_ip_case1()
        if ip_address:
            return ip_address
        ip_address = CSPGenericClass.get_host_public_ip_case2()
        if ip_address:
            return ip_address
        ip_address = CSPGenericClass.get_host_public_ip_case3()
        if ip_address:
            return ip_address
        logger.error("Failed to find your external IP address after attempts to 3 different sites.")
        raise Exception("Failed to find your external IP address. Your internet connection might be broken.")

    def __init__(self, config_parser, client_id=None, secret_id=None, region=None,
            instance_type=None, ssh_key=None, security_group=None, instance_id=None,
            instance_url=None):
        self.config_parser = config_parser
        self.client_id = self.get_from_config('csp', 'client_id', overwrite=client_id)
        self.secret_id = self.get_from_config('csp', 'secret_id', overwrite=secret_id)
        self.region = self.get_from_config('csp', 'region', overwrite=region)
        self.instance_type = self.get_from_config('csp', 'instance_type', overwrite=instance_type)
        self.ssh_key = self.get_from_config('csp', 'ssh_key', overwrite=ssh_key, default="MySSHKey")
        self.security_group = self.get_from_config('csp', 'security_group', overwrite=security_group, default="MySecurityGroup")
        self.instance_id = self.get_from_config('csp', 'instance_id', overwrite=instance_id)
        self.instance_url = self.get_from_config('csp', 'instance_url', overwrite=instance_url)
        self.create_SSH_folder()      # If not existing create SSH folder in HOME folder

    def create_SSH_folder(self):
        self.ssh_dir = os.path.expanduser('~/.ssh')
        if not os.path.isdir(self.ssh_dir):
            os.mkdir(self.ssh_dir, 0o700)

    def create_SSH_key_filename(self):
        ssh_key_file = self.ssh_key + ".pem"
        ssh_files = os.listdir( self.ssh_dir )
        if ssh_key_file not in ssh_files:
            return os.path.join(self.ssh_dir, ssh_key_file)
        idx = 1
        while True:
            ssh_key_file = self.ssh_key + "_%d.pem" % idx
            if ssh_key_file not in ssh_files:
                break
            idx += 1
        logger.warn("A SSH key file named '%s' is already existing in ~/.ssh. To avoid overwritting an existing key, the new SSH key file will be named '%s'.", self.ssh_key, ssh_key_file)
        return os.path.join(self.ssh_dir, ssh_key_file)

    def get_from_config(self, section, key, overwrite=None, default=None):
        if overwrite is not None:
            return overwrite
        try:
            new_val = self.config_parser.get(section, key)
            if new_val:
                return new_val
            return default
        except:
            return default



#===================================
class AWSClass(CSPGenericClass):
#===================================
    def __init__(self, provider, config_parser, **kwargs):
        self.provider = provider
        role = CSPGenericClass.get_from_args('role', **kwargs)
        super(AWSClass, self).__init__(config_parser, **kwargs)
        self.role = self.get_from_config('csp', 'role', overwrite=role)
        if self.role is None:
            raise Exception("No 'role' field has been specified for %s" % self.provider)
        self.load_session()
        self.instance = None
        self.config_env = {}

    def __str__(self):
        return ', '.join("%s:%s" % item for item in vars(self).items())

    def load_session(self):
        try :
            import boto3
            self.session = boto3.session.Session(
                aws_access_key_id = self.client_id,
                aws_secret_access_key = self.secret_id,
                region_name = self.region
            )
        except:
            logger.exception("Caught following exception:")
            raise Exception("Could not authenticate to your %s account", self.provider)

    def check_csp_credential(self):
        try :
            ec2 = self.session.client('ec2')
            response = ec2.describe_key_pairs()
            logger.debug("Response of 'describe_key_pairs': %s", str(response))
            return True
        except:
            logger.exception("Failed to authenticate with your CSP access key.")
            return False

    def ssh_key_csp(self):
        try:
            logger.debug("Create or check if KeyPair "+str(self.ssh_key)+" exists.")
            try :
                ec2 = self.session.client('ec2')
                key_pair = ec2.describe_key_pairs( KeyNames=[self.ssh_key])
                logger.info("KeyPair '%s' is already existing on %s.", str(key_pair['KeyPairs'][0]['KeyName']), self.provider)
            except Exception as e:
                # Key does not exist on the CSP, create it.
                logger.debug(str(e))
                logger.info("Create KeyPair %s", str(self.ssh_key))
                ec2 = self.session.resource('ec2')
                key_pair = ec2.create_key_pair(KeyName=self.ssh_key)
                ssh_key_file = self.create_SSH_key_filename()
                logger.debug("Creating private ssh key file: %s", ssh_key_file)
                with open(ssh_key_file, "w") as text_file:
                    text_file.write(key_pair.key_material)
                os.chmod(ssh_key_file, 0o400)
                logger.debug("Key Content: %s", str(key_pair.key_material))
                logger.info("New SSH Key '%s' has been written in '%s'", ssh_key_file, self.ssh_dir)
            return True
        except:
            logger.exception("Failed to create SSH Key with exception:")
            return False

    def policy_csp(self, policy):
        try:
            logger.debug("Create or check if policy "+str(policy)+" exists.")
            try :
                iam = self.session.client('iam')
                # Create a policy
                my_managed_policy = {   "Version": "2012-10-17",
                                        "Statement": [
                                            {
                                                "Sid": "AllowFpgaCommands",
                                                "Effect": "Allow",
                                                "Action": [
                                                    "ec2:AssociateFpgaImage",
                                                    "ec2:DisassociateFpgaImage",
                                                    "ec2:DescribeFpgaImages"
                                                ],
                                                "Resource": ["*"]
                                            }
                                        ]
                                    }
                response = iam.create_policy( PolicyName=policy, PolicyDocument=json.dumps(my_managed_policy))
                logger.debug("Policy: %s", str(response))
                logger.info("Policy: %s created", str(instance_profile_name))
            except Exception as e:
                logger.debug(str(e))
                logger.info("Policy on AWS named: %s already exists, nothing to do.", str(policy))

            iam = self.session.client('iam')
            response = iam.list_policies( Scope='Local', OnlyAttached=False, MaxItems=100)
            for policyitem in response['Policies']:
                if policyitem['PolicyName'] == policy :
                    return policyitem['Arn']
            return None
        except:
            logger.exception("Failed to create policy with exception:")
            return None

    def role_csp(self):
        try :
            logger.debug("Create or check if role %s exists", str(self.role))
            try :
                iam = self.session.resource('iam')
                role = iam.create_role(RoleName=self.role,
                    AssumeRolePolicyDocument='{ "Version": "2012-10-17", "Statement": {"Effect": "Allow", "Principal": {"Service": "ec2.amazonaws.com"},    "Action": "sts:AssumeRole"  }}',
                    Description='Created automaticly'
                )
                logger.debug("role: %s", str(role))
            except Exception as e:
                logger.debug(str(e))
                logger.info("Role on AWS named: %s already exists, nothing to do.", str(self.role))
            iam = self.session.client('iam')
            response = iam.get_role( RoleName=self.role )
            logger.debug( "Policy ARN:"+str(response['Role']['Arn'])+" already exists.")
            return response['Role']['Arn']
        except:
            logger.exception("Failed to create role with exception:")
            return None

    def attach_role_policy_csp(self,policy):
        try:
            logger.debug("Create or check if policy "+str(policy)+" is attached to role "+str(self.role)+" exists.")
            try :
                iam = self.session.client('iam')
                # Create a policy
                response =iam.attach_role_policy(PolicyArn=policy, RoleName=self.role)
                logger.debug("Policy: "+str(response))
                logger.info("Attached policy "+str(policy)+" to role "+str(self.role)+" done.")
            except Exception as e:
                logger.debug(str(e))
                logger.info("Role on AWS named: "+str(self.role)+" and policy named:"+str(policy)+" already attached, nothing to do.")
            return True
        except:
            logger.exception("Failed to attach policy to role with exception:")
            return False

    def instance_profile_csp(self):
        try:
            instance_profile_name ='AccelizeLoadFPGA'
            logger.debug("Create or check if instance profile  "+str(instance_profile_name)+" exists.")
            try :
                iam = self.session.client('iam')
                instance_profile = iam.create_instance_profile( InstanceProfileName=instance_profile_name)
                time.sleep(5)
                instance_profile.add_role( RoleName=self.role)
                logger.debug("Instance profile: %s", str(instance_profile))
                logger.info("Instance profile %s created", str(instance_profile_name))
            except Exception as e:
                logger.debug(str(e))
                logger.info( "Instance profile on AWS named: :"+str(instance_profile_name)+" already exists, nothing to do.")
            return True
        except:
            logger.exception("Failed to attach policy to role with exception:")
            return False

    def security_group_csp(self):
        try:
            logger.debug("Create or Check if security group '%s' exists.", self.security_group)
            ec2 = self.session.client('ec2')
            public_ip = CSPGenericClass.get_host_public_ip()    # Find the host public IP
            try :
                response = ec2.describe_vpcs()
                vpc_id = response.get('Vpcs', [{}])[0].get('VpcId', '')
                logger.info( "Default VPC: "+str(vpc_id))
                response_create_security_group = ec2.create_security_group(GroupName=self.security_group,
                             Description="Generated by accelize API", VpcId=vpc_id)
                security_group_id = response_create_security_group['GroupId']
                logger.info("Created security group with ID %s in vpc %s", security_group_id, vpc_id)
            except Exception as e:
                logger.debug(str(e))
                logger.info( "A security group '%s' is already existing on %s.", self.security_group, self.provider)
            my_sg = ec2.describe_security_groups( GroupNames=[self.security_group,],)
            try :
                my_sg = ec2.describe_security_groups(GroupNames=[self.security_group,],)
                data = ec2.authorize_security_group_ingress(
                        GroupId=my_sg['SecurityGroups'][0]['GroupId'],
                        IpPermissions=[
                            {'IpProtocol': 'tcp',
                             'FromPort': 80,
                             'ToPort': 80,
                             'IpRanges': [{'CidrIp': public_ip}]
                            },
                            {'IpProtocol': 'tcp',
                             'FromPort': 22,
                             'ToPort': 22,
                             'IpRanges': [{'CidrIp': public_ip}]
                            }
                        ])
                logger.debug( "Successfully Set "+str(data))
                logger.info("Added in security group '%s': SSH and HTTP for IP %s.", self.security_group, public_ip)
            except Exception as e:
                logger.debug(str(e))
                logger.info( "Right for IP "+str(public_ip)+" on AWS already exists, nothing to do.")
            return True
        except:
            logger.exception("Failed to create security group with message:")
            return False

    def get_instance_csp(self):
        if self.instance_id is None:
            logger.warn("No instance ID provided")
            return False
        ec2 = self.session.resource('ec2')
        self.instance = ec2.Instance(self.instance_id)
        try:
            logger.debug("Found an instance with ID %s in the following state: %s", self.instance_id, str(self.instance.state))
            return True
        except:
            logger.error("Could not find an instance with ID %s", self.instance_id)
            return False

    def set_accelerator_requirements(self, accel_parameters):
        if self.region not in accel_parameters.keys():
            logger.error("Region '%s' is not supported. Available regions are: %s", self.region, ', '.join(accel_parameters.keys()))
            return False
        self.accelerator = accel_parameters['accelerator']
        accel_parameters_in_region = accel_parameters[self.region]
        self.config_env = {'AGFI': accel_parameters_in_region['fpgaimage']}
        self.imageId = accel_parameters_in_region['image']
        logger.debug("Set image ID: %s", self.imageId)
        self.instance_type = accel_parameters_in_region['instancetype']
        logger.debug("Set instance type: %s", self.instance_type)
        return True

    def get_configuration_env(self, **kwargs):
        newenv = dict()
        agfi = self.get_from_args('AGFI', **kwargs)
        if agfi:
            newenv['AGFI'] = agfi
        currenv = copy.deepcopy(self.config_env)
        currenv.update(newenv)
        if newenv:
            logger.warn("Overwrite factory requirements with custom configuration:\n%s", pretty_dict(currenv))
        else:
            logger.debug("Using factory configuration: %s", pretty_dict(currenv))
        return currenv

    def create_instance_csp(self):
        if not self.ssh_key_csp():
            return False
        policy_arn = self.policy_csp('AccelizePolicy')
        if policy_arn is None:
            return False
        if self.role_csp() is None:
            return False
        if not self.instance_profile_csp():
            return False
        if not self.attach_role_policy_csp(policy_arn):
            return False
        if not self.security_group_csp():
            return False
        return True

    def get_instance_url(self):
        if self.instance is None:
            return None
        return "http://%s" % str(self.instance.public_ip_address)

    def wait_instance_ready(self):
        try:
            # Waiting for the instance provisioning
            logger.info("Waiting for the instance provisioning on %s...", self.provider)
            while True:
                if not self.get_instance_csp():  # Absolutely mandatory to refresh the state of object (state is not updated automatically)
                    return None
                status = self.instance.state["Name"]
                logger.debug("Instance status: %s", status)
                if status == "running":
                    break
                time.sleep(5)
            # Waiting for the instance to boot
            logger.info("Instance is now booting...")
            instance_url = self.get_instance_url()
            if not check_url( instance_url, 1, 72, 5 ): # 6 minutes timeout
                logger.error("Timed out while waiting CSP instance to boot.")
                return None
            logger.info("Instance booted!")
            return self.instance
        except:
            logger.exception("Caught following exception:")
            return None

    def start_new_instance_csp(self):
        try :
            logger.debug("Starting instance")
            ec2 = self.session.resource('ec2')
            instance = ec2.create_instances(
                                            ImageId=self.imageId,
                                            InstanceType=self.instance_type,
                                            KeyName=self.ssh_key,
                                            SecurityGroups=[
                                                self.security_group,
                                            ],
                                            IamInstanceProfile={
                                                'Name': 'AccelizeLoadFPGA'
                                            },
                                            InstanceInitiatedShutdownBehavior='stop',
                                            TagSpecifications=[
                                                {
                                                    'ResourceType': 'instance',
                                                    'Tags': [
                                                        {
                                                            'Key': 'Generated',
                                                            'Value': 'Accelize script'
                                                        },
                                                        {
                                                            'Key': 'Name',
                                                            'Value': "Accelize accelerator " + self.accelerator
                                                        },
                                                    ]
                                                },
                                            ],
                                            MinCount=1, MaxCount=1
                                        )
            self.instance = instance[0]
            self.instance_id = self.instance.id
            logger.info("Created instance ID: %s", self.instance_id)
            return self.wait_instance_ready()
        except:
            logger.exception("Caught following exception:")
            return None

    def is_instance_ID_valid(self):
        try:
            if not self.get_instance_csp():
                return False
            logger.info("Using instance ID: %s", self.instance_id)
            return True
        except openstack.compute.ResourceNotFound:
            logger.error("Could not find a instance with ID: %s", self.instance_id)
            return False

    def start_existing_instance_csp(self):
        try:
            if not self.is_instance_ID_valid():
                return False
            state = self.instance.state["Name"]
            if state == "stopped":
                response = self.instance.start()
                logger.debug("start response: %s", str(response))
            elif state != "running":
                logger.error("Instance ID %s cannot be started because it is not in a valid state (%s).", self.instance_id, state)
                return False
            if not self.wait_instance_ready():
                return False
            return True
        except:
            logger.exception("Caught following exception:")
            return False

    def start_instance_csp(self):
        if self.instance_id is None:
            ret = self.start_new_instance_csp()
        else:
            ret = self.start_existing_instance_csp()
        if not ret:
            return False
        logger.info("Region: %s", self.session.region_name)
        logger.info("Private IP: %s", self.instance.private_ip_address)
        logger.info("Public IP: %s", self.instance.public_ip_address)
        logger.info("Your instance is now up and running")
        return True

    def stop_instance_csp(self, terminate=True):
        try:
            if not self.get_instance_csp():
                return False
            if terminate:
                response = self.instance.terminate()
                logger.info("Instance ID %s has been terminated", self.instance_id)
            else:
                response = self.instance.stop()
                logger.info("Instance ID %s has been stopped", self.instance_id)
            logger.debug("Stop response: %s", str(response))
            return True
        except:
            logger.exception("Caught following exception:")
            return False


#===================================
class OpenStackClass(CSPGenericClass):
#===================================
    def __init__(self, provider, config_parser, **kwargs):
        self.provider = provider
        project_id = CSPGenericClass.get_from_args('project_id', **kwargs)
        auth_url = CSPGenericClass.get_from_args('auth_url', **kwargs)
        interface = CSPGenericClass.get_from_args('interface', **kwargs)
        super(OpenStackClass, self).__init__(config_parser, **kwargs)
        self.project_id = self.get_from_config('csp', 'project_id', overwrite=project_id)
        if self.project_id is None:
            raise Exception("No 'project_id' field has been specified for %s" % self.provider)
        self.auth_url = self.get_from_config('csp', 'auth_url', overwrite=auth_url)
        if self.auth_url is None:
            raise Exception("No 'auth_url' field has been specified for %s" % self.provider)
        self.interface = self.get_from_config('csp', 'interface', overwrite=interface)
        if self.interface is None:
            raise Exception("No 'interface' field has been specified for %s" % self.provider)
        self.load_session()
        self.instance = None
        self.config_env = {}

    def __str__(self):
        return ', '.join("%s:%s" % item for item in vars(self).items())

    def load_session(self):
        try :
            import openstack
            self.connection = openstack.connection.Connection(
                region_name=self.region,
                auth=dict(
                    auth_url=self.auth_url,
                    username=self.client_id,
                    password=self.secret_id,
                    project_id=self.project_id
                ),
                compute_api_version='2',
                identity_interface=self.interface
            )
            logger.debug("Connection object created for CSP '%s'", self.provider)
        except:
            logger.exception("Caugth following exception:")
            raise Exception("Could not authenticate to your %s account", self.provider)

    def check_csp_credential(self):
        try :
            network_list = self.connection.network.networks()
            return True
        except:
            logger.exception("Failed to authenticate to CSP '%s'.", self.provider)
            return False

    def ssh_key_csp(self):
        logger.debug("Create or check if KeyPair %s exists", self.ssh_key)
        try:
            key_pair = self.connection.compute.find_keypair(self.ssh_key, ignore_missing=True)
            if key_pair:
                # Use existing key
                logger.info("KeyPair '%s' is already existing on %s.", str(key_pair.name), self.provider)
            else:
                # Create key pair
                logger.debug("Create KeyPair '%s'", self.ssh_key)
                key_pair = self.connection.compute.create_keypair(name=self.ssh_key)
                # Save private key locally if not existing
                ssh_key_file = self.create_SSH_key_filename()
                logger.debug("Creating private ssh key file: %s", ssh_key_file)
                with open(ssh_key_file, "w") as text_file:
                    text_file.write(key_pair.private_key)
                os.chmod(ssh_key_file, 0o400)
                logger.debug("Key Content: %s", str(key_pair.private_key))
                logger.info("New SSH Key '%s' has been written in '%s'", ssh_key_file, self.ssh_dir)
            return True
        except:
            logger.exception("Failed to create SSH Key with message:")
            return False

    def security_group_csp(self):
        try:
            logger.debug("Create or check if securitygroup '%s' exists", self.security_group)
            security_group = self.connection.get_security_group(self.security_group)
            if security_group is None:
                security_group = self.connection.create_security_group(
                    self.security_group, "Generated by accelize API", project_id=self.project_id
                )
                logger.info("Created security group: %s", security_group.name)
                # Create Security Group Rules if not provided
            else:
                logger.info("Security group '%s' is already existing on %s.", self.security_group, self.provider)
            # Verify rules associated to security group
            public_ip = CSPGenericClass.get_host_public_ip()    # Find the host public IP
            # Create rule on SSH
            try:
                self.connection.create_security_group_rule(security_group.id, port_range_min=22, port_range_max=22,
                    protocol="tcp", remote_ip_prefix=public_ip, remote_group_id=None, direction='ingress',
                    ethertype='IPv4', project_id=self.project_id
                )
            except:
            #except openstack.exceptions.HttpException:
                pass
            # Create rule on HTTP
            try:
                self.connection.create_security_group_rule(security_group.id, port_range_min=80, port_range_max=80,
                    protocol="tcp", remote_ip_prefix=public_ip, remote_group_id=None, direction='ingress',
                    ethertype='IPv4', project_id=self.project_id
                )
            except:
            #except openstack.exceptions.HttpException:
                pass
            logger.info("Added in security group '%s': SSH and HTTP for IP %s.", self.security_group, public_ip)
            return True
        except:
            logger.exception("Failed to create securityGroup with message:")
            return False

    def create_instance_csp(self):
        if not self.ssh_key_csp():
            return False
        if not self.security_group_csp():
            return False
        return True

    def set_accelerator_requirements(self, accel_parameters):
        if self.region not in accel_parameters.keys():
            logger.error("Region '%s' is not supported. Available regions are: %s", self.region, ', '.join(accel_parameters.keys()))
            return False
        self.accelerator_name = accel_parameters['accelerator']
        accel_parameters_in_region = accel_parameters[self.region]
        # Get image
        self.imageId = accel_parameters_in_region['image']
        try:
            image = self.connection.compute.find_image(self.imageId)
            image.name
        except:
            logger.exception("Failed to get image information for CSP '%s': ", self.provider)
            custom_message = "The image " + str(self.imageId) + " is not available on your CSP account. Please contact Accelize."
            raise Exception(custom_message)
        logger.debug("Set image '%s' with ID %s", image.name, self.imageId)
        # Get flavor
        flavor_name = accel_parameters_in_region['instancetype']
        try:
            self.instance_type = self.connection.compute.find_flavor(flavor_name).id
        except:
            logger.exception("Failed to get flavor information for CSP '%s': ", self.provider)
            custom_message = "The flavor " + str(flavor_name) + " is not available in your CSP account. Please contact you CSP to subscribe to this flavor."
            raise Exception(custom_message)

        logger.debug("Set flavor '%s' with ID %s", flavor_name, self.instance_type)
        return True

    def get_configuration_env(self, **kwargs):
        return self.config_env

    def get_instance_public_ip(self):
        try:
            for address in self.instance.addresses.values()[0]:
                if address['version'] == 4:
                    return str(address['addr'])
            return None
        except:
            return None

    def get_instance_csp(self):
        if self.instance_id is None:
            return False
        try:
            self.instance = self.connection.get_server(self.instance_id)
            logger.debug("Found an instance with ID %s in the following state: %s", self.instance_id, self.instance.status)
            return True
        except:
            logger.error("Could not find an instance with ID %s", self.instance_id)
            return False

    def get_instance_url(self):
        if self.instance is None:
            return None
        public_ip = self.get_instance_public_ip()
        if public_ip is None:
            return None
        return "http://%s" % public_ip

    def wait_instance_ready(self):
        try:
            # Waiting for the instance provisioning
            logger.info("Waiting for the instance provisioning on %s...", self.provider)
            self.instance = self.connection.compute.wait_for_server(self.instance)
            state = self.instance.status
            logger.debug("Instance status: %s", state)
            if state.lower() == "error":
                logger.error("Instance has an invalid status: %s", state)
                self.stop_instance_csp(True)
                return False
            # Waiting for the instance to boot
            self.instance_url = self.get_instance_url()
            logger.info("Instance is now booting...")
            if not check_url( self.instance_url, 1, 72, 5 ): # 6 minutes timeout
                logger.error("Timed out while waiting CSP instance to boot.")
                return False
            logger.info("Instance booted!")
            return True
        except:
            try:
                self.get_instance_csp()
                msg = self.instance.fault.message
                logger.error("CSP error message: %s ",msg)
            except:
                pass
            logger.exception("Caught following exception:")
            return False

    def start_new_instance_csp(self):
        try :
            logger.debug("Starting instance")
            self.instance = self.connection.compute.create_server(
                name=self.accelerator_name, image_id=self.imageId, flavor_id=self.instance_type,
                key_name=self.ssh_key, security_groups=[{"name":self.security_group}])
            self.instance_id = self.instance.id
            logger.info("Created instance ID: %s", self.instance_id)
            return self.wait_instance_ready()
        except:
            logger.exception("Caught following exception:")
            return False

    def is_instance_ID_valid(self):
        try:
            if not self.get_instance_csp():
                return False
            logger.info("Using instance ID: %s", self.instance_id)
            return True
        except openstack.compute.ResourceNotFound:
            logger.error("Could not find a instance with ID: %s", self.instance_id)
            return False

    def start_existing_instance_csp(self):
        try:
            if not self.is_instance_ID_valid():
                return False
            state = self.instance.status
            logger.debug("Status of instance ID %s: %s", self.instance_id, state)
            if state.lower() == "active":
                logger.debug("Instance ID %s is already in '%s' state.", self.instance_id, state)
                return True
            self.connection.start_server(self.instance)
            if not self.wait_instance_ready():
                logger.error("Error occurred when waiting instance ID '%s' to be ready.", self.instance_id)
                return False
            return True
        except:
            logger.exception("Caught following starting instance ID %s:", self.instance_id)
            return False

    def start_instance_csp(self):
        if self.instance_id is None:
            ret = self.start_new_instance_csp()
        else:
            ret = self.start_existing_instance_csp()
        if not ret:
            return False
        logger.info("Region: %s", self.region)
        public_ip = self.get_instance_public_ip()
        logger.info("Public IP: %s", public_ip)
        logger.info("Your instance is now up and running")
        return True

    def stop_instance_csp(self, terminate=True):
        try:
            if not self.get_instance_csp():
                return False
            if terminate:
                self.connection.delete_server(self.instance)
                logger.info("Instance ID %s has been terminated", self.instance_id)
            else:
                self.connection.stop_server(self.instance)
                logger.info("Instance ID %s has been stopped", self.instance_id)
            return True
        except:
            logger.exception("Caught following exception:")
            return False


#===================================
class OVHClass(OpenStackClass):
#===================================
    def start_instance_csp(self):
        if not super(OVHClass, self).start_instance_csp():
            raise Exception("Failed to create OVH instance, please refer to: https://horizon.cloud.ovh.net")
        return True



#===================================
class CSPClassFactory(object):
#===================================
    def __new__(cls, config_file, provider=None, **kwargs):
        config_parser = ConfigParser.ConfigParser(allow_no_value=True)
        config_parser.read(config_file)
        if provider is None:
            try:
                provider = config_parser.get("csp", "provider")
            except:
                raise Exception("Could not find a 'provider' key in the 'csp' section.")
        logger.info("Targeted CSP: %s.", provider)
        if provider.lower() == 'aws':
            return AWSClass(provider, config_parser, **kwargs)
        elif provider.lower() == 'ovh':
            return OVHClass(provider, config_parser, **kwargs)
        else:
            raise ValueError('Cannot initate a CSP class with this provider:'+str(provider))

################################# CSP material [end] ########################################################


################################# Accelerator Class [begin] ########################################################

#===================================
class AcceleratorClass(object):
#===================================
    '''
    This Class is hiding complexity of using GenericAcceleratorClass and CSPGenericClass
    '''
    def __init__(self, accelerator, config_file=None, provider=None,
                region=None, xlz_client_id=None, xlz_secret_id=None, csp_client_id=None,
                csp_secret_id=None, ssh_key=None, instance_id=None, instance_ip=None):
        global config
        logger.debug("")
        logger.debug("/"*100)
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
        self.sign_handler = SignalHandlerAccelerator()
        self.csp = CSPClassFactory(config_file=config_file, provider=provider, client_id=csp_client_id,
            secret_id=csp_secret_id, region=region, ssh_key=ssh_key, instance_id=instance_id,
            instance_url=instance_url)
        # Create Accelerator object
        config = ConfigParser.ConfigParser(allow_no_value=True)
        config.read(config_file)
        if xlz_client_id is None:
            try:
                xlz_client_id = config.get('accelize', 'client_id')
            except:
                raise Exception("Accelize client ID and secret ID are mandatory. Provide them in the configuration file or through function arguments.")
        if xlz_secret_id is None:
            try:
                xlz_secret_id = config.get('accelize', 'secret_id')
            except:
                raise Exception("Accelize client ID and secret ID are mandatory. Provide them in the configuration file or through function arguments.")
        self.accelerator = GenericAcceleratorClass(accelerator, client_id=xlz_client_id, secret_id=xlz_secret_id)
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

    def get_info_from_result(self, result):
        if 'app' not in result.keys():
            return -1, "No result returned!"
        retcode = result['app']['status']
        msg = result['app']['msg']
        return (retcode, msg)

    def get_profiling_from_result(self, result):
        if 'app' not in result.keys():
            logger.debug("No application information found in result JSON file")
            return None
        if 'profiling' not in result['app'].keys():
            logger.debug("No profiling information found in result JSON file")
            return None
        return result['app']['profiling']

    def get_specific_from_result(self, result):
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
        except:
            logger.exception("Exception occurred:")
            return False

    def configure_accelerator(self, datafile=None, accelerator_parameters=None, **kwargs):
        try :
            logger.debug("Configuring accelerator '%s' on instance ID %s", self.accelerator.name, self.csp.instance_id)
            if not check_url(self.accelerator.get_url(), 10):
                return False, {'app': {'status':-1, 'msg':"Failed to reach accelerator url: %s" % self.accelerator.get_url()}}
            csp_env = self.csp.get_configuration_env(**kwargs)
            configResult = self.accelerator.start_accelerator(datafile=datafile, accelerator_parameters=accelerator_parameters, csp_env=csp_env)
            ret, msg = self.get_info_from_result(configResult)
            if ret:
                logger.error("Configuration of accelerator failed: %s", msg)
                return False, configResult
            logger.info("Configuration of accelerator is complete")
            return True, configResult
        except:
            logger.exception("Exception occurred:")
            return False, {'app': {'status':-1, 'msg':"Exception occurred"}}

    def start(self, stop_mode=None, datafile=None, accelerator_parameters=None, **kwargs):
        try:
            # Start a new instance or use a running instance
            if not self.start_instance(stop_mode):
                return False, {'app': {'status':0, 'msg':"Failed to create instance on %s" % self.csp.provider}}
            # Configure accelerator if needed
            if kwargs or (self.accelerator.accelerator_configuration_url is None) or datafile is not None :
                return self.configure_accelerator(datafile, accelerator_parameters, **kwargs)
            logger.debug("Accelerator is already configured")
            return True, {'app': {'status':0, 'msg':"Reusing last configuration: %s" % self.accelerator.accelerator_configuration_url}}
        except:
            logger.exception("Exception occurred:")
            return False, {'app': {'status':-1, 'msg':"Exception occurred"}}

    def process(self,  file_out, file_in=None, process_parameter=None):
        try :
            logger.debug("Starting a processing job: in=%s, out=%s", file_in, file_out)
            if file_in and not os.path.isfile(file_in):
                logger.error("Could not find input file: %s", file_in)
                return False, {'app': {'status':-1, 'msg':"Invalid input file path: %s" % file_in}}
            accel_url = self.accelerator.get_url()
            logger.debug("Accelerator URL: %s", accel_url)
            if not check_url(accel_url, 10):
                return False, {'app': {'status':-1, 'msg':"Failed to reach accelerator url: %s" % self.accelerator.get_url()}}
            processResult = self.accelerator.process_file(file_in=file_in, file_out=file_out, accelerator_parameters=process_parameter)
            profiling = self.get_profiling_from_result(processResult)
            if profiling is not None:
                totalBytes = 0
                globalTime = 0.0
                fpgaTime = 0.0
                if 'wall-clock-time' in profiling.keys():
                    globalTime = float(profiling['wall-clock-time'])
                else:
                    logger.debug("No 'wall-clock-time' found in output JSON file.")
                if 'fpga-elapsed-time' in profiling.keys():
                    fpgaTime = float(profiling['fpga-elapsed-time'])
                else:
                    logger.debug("No 'fpga-elapsed-time' found in output JSON file.")
                if 'total-bytes-written' in profiling.keys():
                    totalBytes += int(profiling['total-bytes-written'])
                else:
                    logger.debug("No 'total-bytes-written' found in output JSON file.")
                if 'total-bytes-read' in profiling.keys():
                    totalBytes += int(profiling['total-bytes-read'])
                else:
                    logger.debug("No 'total-bytes-read' found in output JSON file.")
                logger.info("Profiling information from result:\n%s", json.dumps(profiling, indent=4).replace('\\n','\n').replace('\\t','\t'))
                if totalBytes > 0 and globalTime > 0.0:
                    bw = totalBytes / globalTime / 1024 / 1024
                    fps = 1.0 / globalTime
                    logger.debug("Server processing bandwidths on %s: round-trip = %0.1f MB/s, frame rate = %0.1f fps", self.csp.provider, bw, fps)
                if totalBytes > 0 and fpgaTime > 0.0:
                    bw = totalBytes / fpgaTime / 1024 / 1024
                    fps = 1.0 / fpgaTime
                    logger.debug("FPGA processing bandwidths on %s: round-trip = %0.1f MB/s, frame rate = %0.1f fps", self.csp.provider, bw, fps)
            specific = self.get_specific_from_result(processResult)
            if specific is not None and len(specific.keys()):
                logger.info("Specific information from result:\n%s", json.dumps(specific, indent=4).replace('\\n','\n').replace('\\t','\t'))
            ret, msg = self.get_info_from_result(processResult)
            bRet = False if ret else True
            return bRet, processResult
        except:
            logger.exception("Exception occurred:")
            return False, {'app': {'status':-1, 'msg':"Exception occurred"}}

    def stop_accelerator(self):
        logger.debug("Stopping accelerator '%s' on instance ID %s", self.accelerator.name, self.csp.instance_id)
        try :
            if not check_url(self.accelerator.get_url(), 10):
                return False, {'app': {'status':-1, 'msg':"Failed to reach accelerator url: %s" % self.accelerator.get_url()}}
            stopResult = self.accelerator.stop_accelerator()
            ret, msg = self.get_info_from_result(stopResult)
            if ret:
                logger.error("Stopping accelerator failed: %s", msg)
                return False, stopResult
            logger.info("Accelerator session is closed")
            return True, stopResult
        except:
            logger.exception("Exception occurred:")
            return False, {'app': {'status':-1, 'msg':"Exception occurred"}}

    def stop_instance(self, terminate=True):
        logger.debug("Stopping instance (ID: %s) on '%s'", self.csp.instance_id, self.csp.provider)
        try:
            res = self.stop_accelerator()
            self.csp.stop_instance_csp(terminate)
            self.sign_handler.remove_instance()
            return res
        except:
            logger.exception("Exception occurred:")
            return False, {'app': {'status':-1, 'msg':"Exception occurred"}}

    def stop(self, stop_mode=None):
        try:
            if stop_mode is None:
                stop_mode = self.sign_handler.stop_mode
            if stop_mode == KEEP:
                return self.stop_accelerator()
            terminate = True if stop_mode == TERM else False
            return self.stop_instance(terminate)
        except:
            logger.exception("Exception occurred:")
            return False, {'app': {'status':-1, 'msg':"Exception occurred"}}


################################# Accelerator Class [end] ########################################################
