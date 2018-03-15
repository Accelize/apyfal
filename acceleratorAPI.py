__version__ = "1.3"

import os
import sys
import inspect
import logging
import logging.handlers
import time
import signal
import shutil
import copy
import urllib3
import ast
import json
import requests
import socket
import ConfigParser


import rest_api.swagger_client
from rest_api.swagger_client.rest import ApiException

# Module logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARN)

# Rotating file handler
LOG_FILENAME = os.path.basename(__file__).replace(".py",".log")
MAX_BYTES = 100*1024*1024
fileHandler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=MAX_BYTES, backupCount=5)
fileHandler.setLevel(logging.DEBUG)
fileHandler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)-8s: %(name)-20s, %(funcName)-28s, %(lineno)-4d: %(message)s"))
logger.addHandler(fileHandler)

DEFAULT_CONFIG_FILE = "accelerator.conf"

TERM = 0
STOP = 1
KEEP = 2


def checkUrl(url, timeout=None, retryCount=0, retryPeriod=5):
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
                logger.debug("Check URL server: %s ...", url)
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


def prettyDict(obj):
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

    def add_instance(self, instance):
        self.csp = instance
        logger.debug("Added instance to auto-stop handler.")

    def remove_instance(self):
        ret = self.csp.get_instance_csp()
        if ret:
            logger.debug("Removed instance ID %s from to auto-stop handler.", self.csp.instance.id)
        self.csp = None

    def set_stop_mode(self, stop_mode):
        self.stop_mode = int(stop_mode)
        logger.info("Auto-stop mode now is: %s", self.STOPMODE[self.stop_mode])

    def set_signals(self):
        '''Set a list of interrupt signals to be handled asynchronously'''
        signal.signal(signal.SIGTERM, self.signal_handler_accelerator)
        signal.signal(signal.SIGINT, self.signal_handler_accelerator)
        signal.signal(signal.SIGQUIT, self.signal_handler_accelerator)

    def signal_handler_accelerator(self, _signo="", _stack_frame="", exit=True):
        '''Try to stop all instances running or inform user'''
        if self.csp is None:
            logger.debug("There is no registered instance to stop")
        elif self.csp.get_instance_csp():
            if self.stop_mode == KEEP:
                logger.warn("###########################################################")
                logger.warn("## Warning : instance ID '%s' is still running!", self.csp.instance.id)
                logger.warn("###### Make sure you will stop it manually. #######")
                logger.warn("###########################################################")
            elif self.csp.instance.id:
                terminate = True if self.stop_mode == TERM else False
                self.csp.stop_instance_csp(terminate)
        if exit:
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
            r = requests.post('https://master.metering.accelize.com/o/token/',data={"grant_type":"client_credentials"} , auth=(self.client_id, self.secret_id))
            if r.status_code != 200 :
                logger.error("Accelize authentication failed: %s", r.text)
                return False
            logger.info("Accelize authentication is successful")
            return True
        except:
            logger.exception("Caught following exception:")
            return False

    def setUrl(self, url):
        self.api_configuration.host = url

    def getUrl(self):
        return self.api_configuration.host

    def get_accelerator_requirements(self, provider):
        try :
            r = requests.post('https://master.metering.accelize.com/o/token/',data={"grant_type":"client_credentials"} , auth=(self.client_id, self.secret_id))
            logger.debug( "Accelize token answer: %s", str(r.text))
            r.raise_for_status()
            if r.status_code == 200 :
                #call WS
                answer_token = json.loads(r.text)
                headers = {"Authorization": "Bearer "+str(answer_token['access_token']),"Content-Type":"application/json","Accept":"application/vnd.accelize.v1+json"}
                r = requests.get('https://master.metering.accelize.com/auth/getlastcspconfiguration/',headers=headers)
                logger.debug( "Accelize config answer: %s, status: %s", r.text , str(r.status_code))
                r.raise_for_status()
                configuration_accelerator = json.loads(r.text)
                logger.debug("Accelerator requirements:\n%s", prettyDict(configuration_accelerator))
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
            logger.debug("Get list of configurations...")
            api_response = api_instance.configuration_list()
            configList = api_response.results
            logger.debug("configuration_list api_response:\n%s", prettyDict(api_response))
            #if api_response.inerror :
            #    raise ValueError("Cannot get list of configurations")
            #    return None
            return configList
        except ApiException:
            logger.exception("Caught following exception while calling ConfigurationApi->configuration_list:")
            return None
        except Exception as e:
            logger.exception("Caught following exception:")
            return None

    def use_last_configuration(self):
        # Get last configuration, if any
        configList = self.get_accelerator_configuration_list()
        if not configList:
            logger.warn("Accelerator has not been configured yet.")
            return False
        last_config = configList[0]
        logger.debug("Last recorded configuration: Url:%s, Used:%d", last_config.url, last_config.used)
        if last_config.used == 0:
            logger.warn("Accelerator has no active configuration. It needs to be configured before being used.")
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
            if accelerator_parameters is None:
                logger.debug( "Using default configuration parameters")
                accelerator_parameters = ast.literal_eval(config.get("configuration", "parameters"))
            envserver = { "client_id":self.client_id, "client_secret":self.secret_id }
            envserver.update(csp_env)
            parameters = {"env":envserver, "app":accelerator_parameters}
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
            dictparameters['url_config']= api_response.url
            dictparameters['url_instance']= self.api_configuration.host
            logger.debug("status: %s", str(dictparameters['app']['status']) )
            logger.debug("msg:\n%s", dictparameters['app']['msg'] )
            api_response_read = api_instance.configuration_read(id)
            if api_response_read.inerror:
                return {'app': {'status':-1, 'msg':"Cannot start the configuration %s" % api_response_read.url}}
            return dictparameters
        except ApiException:
            logger.exception("Caught following exception while calling ConfigurationApi->configuration_create:")
            return {'app': {'status':-1, 'msg':str(e)}}
        except Exception as e:
            logger.exception("Caught following exception:")
            return {'app': {'status':-1, 'msg':str(e)}}

    def process_file(self, file_in, file_out, accelerator_parameters=None) :
        if self.accelerator_configuration_url is None:
            logger.error("Accelerator has not been configured. Use 'start_accelerator' function.")
            return {'app': {'status':-1, 'msg':"Accelerator is not configured."}}
        # create an instance of the API class
        api_instance = rest_api.swagger_client.ProcessApi(api_client=self.api_configuration.api_client)
        if accelerator_parameters == None:
            logger.debug( "Using default processing parameters")
            accelerator_parameters = ast.literal_eval(config.get("process", "parameters"))
        logger.info("Using configuration: %s", self.accelerator_configuration_url)
        datafile = file_in # file | If needed, file to be processed by the accelerator. (optional)
        try:
            try: # Bypass REST API because upload issue with big file using python https://bugs.python.org/issue8450
                import pycurl
                from StringIO import StringIO
                logger.debug( "pycurl process=%s datafile=%s", self.accelerator_configuration_url, str(datafile) )
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
                c.close()
                content = storage.getvalue()
                logger.debug( "pycurl process:"+str(content) )
                r2 = json.loads(content)
                if 'id' not in r2.keys():
                    logger.error("Processing failed with no message (host application did not run).")
                    return {'app': {'status':-1, 'msg':""}}
                id = r2['id']
                processed = r2['processed']
            except ImportError:
                logger.debug( "process_create process=%s datafile=%s", self.accelerator_configuration_url, str(datafile) )
                api_response = api_instance.process_create(self.accelerator_configuration_url, parameters=json.dumps(accelerator_parameters), datafile=datafile)
                id = api_response.id
                processed = api_response.processed
            while processed != True :
                api_response = api_instance.process_read(id)
                processed = api_response.processed
                if api_response.inerror :
                    msg = "Cannot start the process: %s" % prettyDict(api_response.parametersresult)
                    logger.error(msg)
                    return {'app': {'status':-1, 'msg':msg}}
            http = urllib3.PoolManager()
            with http.request('GET', api_response.datafileresult, preload_content=False) as r, open(file_out, 'wb') as out_file:
                shutil.copyfileobj(r, out_file)
            logger.debug( "process_delete api_response: "+str(id) )
            api_response_delete = api_instance.process_delete(id)
            dictparameters = ast.literal_eval(api_response.parametersresult)
            logger.debug(  "status:"+str(dictparameters['app']['status']))
            logger.debug(  "msg:\n"+dictparameters['app']['msg'])
            return dictparameters
        except ApiException as e:
            logger.error("Caught following exception while calling ProcessApi->process_create: %s", str(e))
            return {'app': {'status':-1, 'msg':str(e)}}
        except:
            logger.exception("Caught following exception:")
            return {'app': {'status':-1, 'msg':"Caugth unsupported exception"}}

    def stop_accelerator(self):
        # create an instance of the API class
        api_instance = rest_api.swagger_client.StopApi(api_client=self.api_configuration.api_client)
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
    def getFromArgs(key, **kwargs):
        try:
            return kwargs.pop(key)
        except:
            return None

    def __init__(self, config_parser, client_id=None, secret_id=None, region=None,
            instance_type=None, ssh_key=None, security_group=None, instance_id=None,
            instance_url=None):
        self.config_parser = config_parser
        self.client_id = self.getFromConfig('csp', 'client_id', client_id)
        self.secret_id = self.getFromConfig('csp', 'secret_id', secret_id)
        self.region = self.getFromConfig('csp', 'region', region)
        self.instance_type = self.getFromConfig('csp', 'instance_type', instance_type)
        self.ssh_key = self.getFromConfig('csp', 'ssh_key', ssh_key)
        if self.ssh_key is None:
            self.ssh_key = "MySSHKey"
        self.security_group = self.getFromConfig('csp', 'security_group', security_group)
        if self.security_group is None:
            self.security_group = "MySecurityGroup"
        self.instance_id = self.getFromConfig('csp', 'instance_id', instance_id)
        self.instance_url = self.getFromConfig('csp', 'instance_url', instance_url)

    def getFromConfig(self, section, key, default=None):
        if default:
            return default
        try:
            new_val = self.config_parser.get(section, key)
            if new_val:
                return new_val
            else:
                return None
        except:
            return None

    def get_public_ip(self):
        try :
            r = requests.get('http://ipinfo.io/ip')
            logger.debug("Public IP answer: %s", str(r.text))
            r.raise_for_status()
            return r.text.strip()+"/32"
        except:
            logger.exception("Caught following exception:")
            raise Exception("Cannot get your current pubblic IP address")


#===================================
class AWSClass(CSPGenericClass):
#===================================
    def __init__(self, provider, config_parser, **kwargs):
        self.provider = provider
        role = CSPGenericClass.getFromArgs('role', **kwargs)
        super(AWSClass, self).__init__(config_parser, **kwargs)
        self.role = self.getFromConfig('csp', 'role', role)
        if self.role is None:
            raise Exception("No 'role' field has been specified for %s" % self.provider)
        self.instance = None
        self.config_env = {}

    def __str__(self):
        return ', '.join("%s:%s" % item for item in vars(self).items())

    def loadsession(self):
        try :
            import boto3
            self.session = boto3.session.Session(
                aws_access_key_id = self.client_id,
                aws_secret_access_key = self.secret_id,
                region_name = self.region
            )
            return True
        except:
            logger.exception("Caught following exception:")
            return False

    def check_csp_credential(self):
        try :
            if not self.loadsession():
                return False
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
                logger.info( "KeyPair on AWS named: "+str(key_pair['KeyPairs'][0]['KeyName'])+" already exists, nothing to do.")
                return True
            except Exception as e:
                logger.debug(str(e))
                logger.info("Create KeyPair %s", str(self.ssh_key))
                ec2 = self.session.resource('ec2')
                key_pair = ec2.create_key_pair(KeyName=self.ssh_key)
                with open(self.ssh_key+".pem", "w") as text_file:
                    text_file.write(key_pair.key_material)
                os.chmod(self.ssh_key+".pem", 0600)
                logger.debug("Key Content: %s", str(key_pair.key_material))
                logger.info("Key write in the current directory: %s.pem", self.ssh_key)
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
            public_ip = self.get_public_ip()
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
                logger.info( "A security group '%s' is already existing on AWS.", self.security_group)
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

    def wait_instance_ready(self):
        try:
            # Waiting for the instance provisioning
            logger.info("Waiting for the instance provisioning...")
            while True:
                if not self.get_instance_csp():  # Absolutely mandatory to update the state of object (state is not updated automatically)
                    return None
                status = self.instance.state["Name"]
                logger.debug("Instance status: %s", status)
                if status == "running":
                    break
                time.sleep(5)
            # Waiting for the instance to boot
            logger.info("Instance is now booting")
            url = "http://%s" % str(self.instance.public_ip_address)
            if not checkUrl( url, 1, 72, 5 ): # 6 minutes timeout
                logger.error("Timed out while waiting CSP instance to boot.")
                return None
            logger.info("Instance booted!")
            return self.instance
        except:
            logger.exception("Caught following exception:")
            return None

    def get_instance_csp(self):
        if self.instance_id is None:
            logger.error("Invalid instance ID: %s", str(self.intance_id))
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

    def getConfigurationEnv(self, **kwargs):
        newenv = dict()
        agfi = self.getFromArgs('AGFI', **kwargs)
        if agfi:
            newenv['AGFI'] = agfi
        currenv = copy.deepcopy(self.config_env)
        currenv.update(newenv)
        if newenv:
            logger.warn("Overwrite factory requirements with custom configuration:\n%s", prettyDict(currenv))
        else:
            logger.debug("Using factory configuration: %s", prettyDict(currenv))
        return currenv

    def create_instance_csp(self):
        #call webservice
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

    def start_existing_instance_csp(self):
        try:
            if not self.get_instance_csp():
                return False
            logger.info("Using instance ID: %s", self.instance_id)
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
        self.instance_url = "http://%s" % self.instance.public_ip_address
        logger.info("Your instance is now up and running")
        return True

    def stop_instance_csp(self, terminate=True):
        try:
            if not self.get_instance_csp():
                return False
            if terminate:
                logger.info("Terminating instance ID %s", self.instance_id)
                response = self.instance.terminate()
            else:
                logger.info("Stopping instance ID %s", self.instance_id)
                response = self.instance.stop()
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
        project_id = CSPGenericClass.getFromArgs('project_id', **kwargs)
        auth_url = CSPGenericClass.getFromArgs('auth_url', **kwargs)
        interface = CSPGenericClass.getFromArgs('interface', **kwargs)
        provider = config_parser.get('csp', 'provider')
        super(OpenStackClass, self).__init__(config_parser, **kwargs)
        self.project_id = self.getFromConfig('csp', 'project_id', project_id)
        if self.project_id is None:
            raise Exception("No 'project_id' field has been specified for %s" % self.provider)
        self.auth_url = self.getFromConfig('csp', 'auth_url', auth_url)
        if self.auth_url is None:
            raise Exception("No 'auth_url' field has been specified for %s" % self.provider)
        self.interface = self.getFromConfig('csp', 'interface', interface)
        if self.interface is None:
            raise Exception("No 'interface' field has been specified for %s" % self.provider)
        self.connection = None
        self.instance = None
        self.config_env = {}

    def __str__(self):
        return ', '.join("%s:%s" % item for item in vars(self).items())

    def loadsession(self):
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
            return True
        except:
            logger.exception("Caugth following exception:")
            return False

    def check_csp_credential(self):
        try :
            if not self.loadsession():
                return False
            network_list = self.connection.network.networks()
            self.connection.compute.find_keypair("FPGAOVH", ignore_missing=True)
            return True
        except:
            logger.exception("Failed to authenticate to CSP '%s'.", self.provider)
            return False

    def ssh_key_csp(self):
        logger.debug("Create or check if KeyPair %s exists", self.ssh_key)
        try:
            ssh_dir = os.path.expanduser('~/.ssh')
            private_keypair_file = os.path.join(ssh_dir, "%s.pem" % self.ssh_key)
            logger.info("Check if KeyPair '%s' exists and create it if not.", self.ssh_key)
            keypair = self.connection.compute.find_keypair(self.ssh_key, ignore_missing=True)
            if not keypair:
                logger.debug("Create KeyPair '%s'", self.ssh_key)
                keypair = self.connection.compute.create_keypair(name=self.ssh_key)
                # Save private key locally if not existing
                logger.debug("Creating private ssh key file: %s", private_keypair_file)
                if not os.path.isdir(ssh_dir):
                    os.mkdir(ssh_dir, 0o700)
                with open(private_keypair_file, 'w') as f:
                    f.write("%s" % keypair.private_key)
                os.chmod(private_keypair_file, 0o400)
            elif not os.path.isfile(private_keypair_file):
                logger.warn("Could not find a ssh key public file: %s", private_keypair_file)
            else:
                logger.info("KeyPair '%s' is already existing in your home.", self.ssh_key)
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
                logger.info("Security group '%s' is already existing.", self.security_group)
            # Verify rules associated to security group
            public_ip = self.get_public_ip()
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
        image = self.connection.compute.find_image(self.imageId)
        logger.debug("Set image '%s' with ID %s", image.name, self.imageId)
        # Get flavor
        flavor_name = accel_parameters_in_region['instancetype']
        self.instance_type = self.connection.compute.find_flavor(flavor_name).id
        logger.debug("Set flavor '%s' with ID %s", flavor_name, self.instance_type)
        return True

    def getConfigurationEnv(self, **kwargs):
        return self.config_env

    def getPublicIp(self):
        public_ip = None
        try:
            for address in self.instance.addresses.values()[0]:
                if address['version'] == 4:
                    public_ip = str(address['addr'])
        except:
            pass
        if public_ip is None:
            logger.error("Failed to get public IP address.")
        return public_ip

    def wait_instance_ready(self):
        try:
            # Waiting for the instance provisioning
            logger.info("Waiting for the instance provisioning...")
            self.instance = self.connection.compute.wait_for_server(self.instance)
            state = self.instance.status
            logger.debug("Instance status: %s", state)
            if state.lower() == "error":
                logger.error("Instance has an invalid status: %s", state)
                self.stop_instance_csp(True)
                return False
            # Waiting for the instance to boot
            self.instance_url = "http://%s" % self.getPublicIp()
            logger.info("Instance is now booting")
            if not checkUrl( self.instance_url, 1, 72, 5 ): # 6 minutes timeout
                logger.error("Timed out while waiting CSP instance to boot.")
                return False
            return True
        except:
            logger.exception("Caught following exception:")
            return False

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
            return None

    def start_existing_instance_csp(self):
        try:
            if not self.get_instance_csp():
                return False
            logger.info("Using instance ID: %s", self.instance_id)
        except openstack.compute.ResourceNotFound:
            logger.error("Could not find a instance with ID: %s", self.instance_id)
            return False
        try:
            state = self.instance.status
            logger.debug("Status of instance ID %s: %s", self.instance_id, state)
            if state != "running":
                logger.error("Instance ID %s is already in %s state.", self.instance_id, state)
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
        public_ip = self.getPublicIp()
        logger.info("Public IP: %s", public_ip)
        self.instance_url = "http://%s" % public_ip
        logger.info("Instance is ready to use!")
        return True

    def stop_instance_csp(self, terminate=True):
        try:
            if not self.get_instance_csp():
                return False
            if terminate:
                logger.info("Terminating instance ID %s", self.instance_id)
                self.connection.delete_server(self.instance)
            else:
                logger.info("Stopping instance ID %s", self.instance_id)
                self.connection.stop_server(self.instance)
            return True
        except:
            logger.exception("Caught following exception:")
            return False


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
        logger.info("Targetting CSP: %s.", provider)
        if provider.lower() == 'aws':
            return AWSClass(provider, config_parser, **kwargs)
        elif provider.lower() == 'ovh':
            return OpenStackClass(provider, config_parser, **kwargs)
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
        self.sign_handler.add_instance(self.csp)
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

    def __del__(self):
        self.sign_handler.signal_handler_accelerator(exit=False)

    # Start a new instance or use a running instance
    def start_instance(self, stop_mode=None):
        stop_mode = self.csp.getFromConfig("csp", "stop_mode", stop_mode)
        if stop_mode:
            self.sign_handler.set_stop_mode(stop_mode)
        # Checking if credentials are valid otherwise no sense to continue
        if not self.accelerator.check_accelize_credential():
            return False
        if self.csp.instance_url is None:
            if not self.csp.check_csp_credential():
                return False
            accel_requirements = self.accelerator.get_accelerator_requirements(self.csp.provider)
            if accel_requirements is None:
                return False
            if not self.csp.set_accelerator_requirements(accel_requirements):
                return False
            if self.csp.instance_id is None:
                if not self.csp.create_instance_csp():
                    return False
            if not self.csp.start_instance_csp():
                return False
        self.accelerator.setUrl(self.csp.instance_url)
        logger.info("Accelerator URL: %s", self.csp.instance_url)
        # If possible use the last accelerator configuration (it can still be overwritten later)
        self.accelerator.use_last_configuration()
        return True

    def getInfoFromResult(self, result):
        if 'app' not in result.keys():
            return -1, "No result returned!"
        retcode = result['app']['status']
        msg = result['app']['msg']
        return (retcode, msg)

    def configure_accelerator(self, datafile=None, accelerator_parameters=None, **kwargs):
        try :
            logger.debug("Configuring accelerator '%s' on instance ID %s", self.accelerator.name, self.csp.instance_id)
            if not checkUrl(self.accelerator.getUrl(), 10):
                return False, {'app': {'status':-1, 'msg':"Failed to reach accelerator url: %s" % self.accelerator.getUrl()}}
            csp_env = self.csp.getConfigurationEnv(**kwargs)
            configResult = self.accelerator.start_accelerator(datafile=datafile, accelerator_parameters=accelerator_parameters, csp_env=csp_env)
            ret, msg = self.getInfoFromResult(configResult)
            if ret:
                logger.error("Configuration of accelerator failed: %s", msg)
                return False, configResult
            logger.info("Configuration of accelerator is complete")
            return True, configResult
        except Exception as e:
            logger.exception("Caught following exception:")
            return False, {'app': {'status':-1, 'msg':"Following error occurred: %s" % str(e)}}

    def start(self, stop_mode=TERM, datafile=None, accelerator_parameters=None, **kwargs):
        logger.debug("Starting accelerator server '%s' on '%s'", self.accelerator.name, self.csp.provider)
        # Start a new instance or use a running instance
        if not self.start_instance(stop_mode):
            return False
        # Configure accelerator if needed
        if kwargs or (self.accelerator.accelerator_configuration_url is None):
            return self.configure_accelerator(datafile, accelerator_parameters, **kwargs)
        logger.debug("Accelerator is already configured")
        return True, {'app': {'status':0, 'msg':"Reusing last configuration: %s" % self.accelerator_configuration_url}}

    def process(self, file_in, file_out, process_parameter=None):
        logger.debug("Starting a processing job: in=%s, out=%s", file_in, file_out)
        try :
            accel_url = self.accelerator.getUrl()
            logger.debug("Accelerator URL: %s", accel_url)
            if not checkUrl(accel_url, 10):
                return False, {'app': {'status':-1, 'msg':"Failed to reach accelerator url: %s" % self.accelerator.getUrl()}}
            processResult = self.accelerator.process_file(file_in=file_in, file_out=file_out, accelerator_parameters=process_parameter)
            ret, msg = self.getInfoFromResult(processResult)
            if ret:
                return False, processResult
            logger.info("Processing on accelerator is complete")
            return True, processResult
        except Exception as e:
            logger.exception("Caught following exception:")
            return False, {'app': {'status':-1, 'msg':"Exception occured: %s" % str(e)}}

    def stop_accelerator(self):
        logger.debug("Stopping accelerator '%s' on instance ID %s", self.accelerator.name, self.csp.instance_id)
        try :
            if not checkUrl(self.accelerator.getUrl(), 10):
                return False, {'app': {'status':-1, 'msg':"Failed to reach accelerator url: %s" % self.accelerator.getUrl()}}
            stopResult = self.accelerator.stop_accelerator()
            ret, msg = self.getInfoFromResult(stopResult)
            if ret:
                logger.error("Stopping accelerator failed: %s", msg)
                return False, stopResult
            logger.info("Stopping accelerator is complete")
            return True, stopResult
        except Exception as e :
            logger.exception("Caught following exception:")
            return False, {'app': {'status':-1, 'msg':"Following error occurred: %s" % str(e)}}

    def stop_instance(self, terminate=True):
        logger.debug("Stopping instance (ID: %s) on '%s'", self.csp.instance_id, self.csp.provider)
        try:
            self.stop_accelerator()
            self.sign_handler.remove_instance()
            self.csp.stop_instance_csp(terminate)
            return True
        except:
            logger.exception("Caught following exception:")
            return False

    def stop(self, stop_mode=None):
        logger.debug("Stopping accelerator '%s' running on '%s' instance ID '%s'", self.accelerator.name, self.csp.provider, self.csp.instance_id)
        try:
            if stop_mode is None:
                stop_mode = self.sign_handler.stop_mode
            if stop_mode == KEEP:
                self.stop_accelerator()
                return True
            terminate = True if stop_mode == TERM else False
            return self.stop_instance(terminate)
        except:
            logger.exception("Caught following exception:")
            return False

    def getInfo(self):
        d = dict()
        d['publicIP'] = self.csp.instance.public_ip_address
        d['privateIP'] = self.csp.instance.private_ip_address
        d['configuration_url'] = self.accelerator.accelerator_configuration_url
        return d


################################# Accelerator Class [end] ########################################################
