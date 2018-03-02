import time
import signal
import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir =  os.path.abspath(os.path.join(os.path.join(os.path.join(os.path.join(currentdir, os.pardir), os.pardir),'REST_API'),'python'))
sys.path.insert(0,parentdir)
import swagger_client
from swagger_client.rest import ApiException
import shutil, urllib3, os
from multiprocessing import Pool
import requests
import json
import logging
import logging.handlers
import socket
import ConfigParser
import os.path
import ast
from urllib2 import urlopen, URLError, HTTPError

__version__ = "0.3"

# Module logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
# Rotating file handler
LOG_FILENAME = os.path.basename(__file__).replace(".py",".log")
MAX_BYTES = 100*1024*1024
fileHandler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=MAX_BYTES, backupCount=5)
fileHandler.setLevel(logging.DEBUG)
fileHandler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)-8s: %(name)-20s, %(funcName)-28s, %(lineno)-4d: %(message)s"))
logger.addHandler(fileHandler)

DEFAULT_CONFIG_FILE = "accelerator.conf"
config = ConfigParser.ConfigParser(allow_no_value=True)

TERM = 0
STOP = 1
KEEP = 2


def ping(url, timeout=None, retryCount=0, retryPeriod=5):
    '''
        Checking if an HTTP is up and running.
    '''
    t = socket.getdefaulttimeout()
    missCnt = 0
    try:
        if timeout is not None:
            socket.setdefaulttimeout( timeout )  # timeout in seconds                
        while missCnt <= retryCount:
            try :
                logger.debug("Pinging server %s ...", url)
                response = urlopen( url )
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


def getVal(val, section, key):
    if val:
        return val
    try:
        new_val = config.get(section, key)
    except:
        return None
    if new_val:
        return new_val
    else:
        return None
    
    
def prettyDict(obj):
    return json.dumps(ast.literal_eval(str(obj)), indent=4)


#===================================
class SignalHandlerAccelerator(object):
#===================================
    '''Signal handler for Instances'''
    STOPMODE = { TERM: "TERM",
                 STOP: "STOP",
                 KEEP: "KEEP" }

    def __init__(self, csp_instance):
        self.instances = []
        self.csp_instance = csp_instance
        self.set_signals()
        self.stop_mode = KEEP

    def append_instance(self, instance_id):
        self.instances.append(instance_id)
        logger.debug("Added instance ID %s", instance_id)

    def remove_instance(self, instance_id):
        self.instances = [x for x in self.instances if x != instance_id]
        logger.debug("Removed instance ID %s from registered instances", instance_id)
        
    def set_stop_mode(self, stop_mode):
        self.stop_mode = int(stop_mode)
        logger.debug("Saved auto-stop mode=%s", self.STOPMODE[self.stop_mode])

    def set_signals(self):
        '''Set a list of interrupt signals to be handled asynchronously'''
        signal.signal(signal.SIGTERM, self.signal_handler_accelerator)
        signal.signal(signal.SIGINT, self.signal_handler_accelerator)
        signal.signal(signal.SIGQUIT, self.signal_handler_accelerator)

    def signal_handler_accelerator(self, _signo="", _stack_frame="", exit=True):
        '''Try to stop all instances running or inform user'''
        if self.stop_mode == KEEP and self.instances:
            logger.warn("###########################################################")
            logger.warn("## Warning : following instances are still running:")
            for instance_id in self.instances:
               logger.warn("#\t- instance ID: %s", instance_id)
            logger.warn("###### Make sure you will stop them manually later. #######")
            logger.warn("###########################################################")
        else:
            terminate = True if self.stop_mode == TERM else False
            if not self.instances:
                logger.debug("There is no registered instance to stop")
            else:
                for instance in self.instances:
                   self.csp_instance.stop_instance_csp(terminate)
        if exit:
            logger.info("Accelerator API Closed properly")
            #os._exit(0)


################################# Rest API material [begin] ########################################################

#===================================
class GenericAcceleratorClass(object):
#===================================
    '''############################################################
    #####  EndUser API based on the openAPI Accelize accelerator
    #####  Objective of this API it to remove complex user actions
    ###############################################################
    '''
#    def __init__(self, accelerator, client_id, secret_id, url='http://localhost'):
    def __init__(self, accelerator, client_id, secret_id, url=None):
        # A regular API has fixed url. In our case we want to change it dynamically.
        self.accelerator = accelerator
        self.api_configuration = swagger_client.Configuration()
#        url = re.search(r"(https?://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", configuration_url).group()
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
                if self.accelerator not in configuration_accelerator[provider].keys():
                    logger.error("Accelerator '%s' is not supported on '%s'.", self.accelerator, provider)
                    return None
                info = configuration_accelerator[provider][self.accelerator]
                info['accelerator'] = self.accelerator
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
            api_instance = swagger_client.ConfigurationApi(api_client=self.api_configuration.api_client)
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
            logger.warn("Accelerator has not been configurated yet.")
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
    def configure_accelerator(self, envserver, accelerator_parameters=None, datafile=None):
        try:
            # /v1.0/configuration/
            # create an instance of the API class
            api_instance = swagger_client.ConfigurationApi(api_client=self.api_configuration.api_client)
            if accelerator_parameters is None:
                logger.debug( "Using default configuration parameters")
                accelerator_parameters = ast.literal_eval(config.get("configuration", "parameters"))
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
            logger.error("Accelerator has not been configured. Use 'configure_accelerator' function.")
            return {'app': {'status':-1, 'msg':"Accelerator is not configured."}}
        # create an instance of the API class
        api_instance = swagger_client.ProcessApi(api_client=self.api_configuration.api_client)
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
                #api_client = Struct(**r2)
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
            dictparameters = eval(api_response.parametersresult)
            logger.debug(  "status:"+str(dictparameters['app']['status']))
            logger.debug(  "msg:\n"+dictparameters['app']['msg'])
            return dictparameters
        except ApiException as e:
            logger.error("Caught following exception while calling ProcessApi->process_create: %s", str(e))
            #logger.exception("Caught following exception while calling ProcessApi->process_create:")
            return {'app': {'status':-1, 'msg':str(e)}}
        except:
            logger.exception("Caught following exception:")
            return {'app': {'status':-1, 'msg':"Caugth unsupported exception"}}

    def process_directory(self,dirsource="",dirdestination="",parameters='{}',processes=4) :
        #if self.accelerator_configuration_url is None:
        #    logger.error("Accelerator has not been configured. Use configure_accelerator")
        #    return {'app': {'status':-1, 'msg':"Accelerator is not configured."}}
        #pool = Pool(processes=processes)              # start 4 worker processes
        for file in os.listdir(dirsource):
            #pool.apply_async(process, (os.path.join(dirsource, file),os.path.join(dirdestination, file),configuration,parameters))
            #pool.apply(self.process, (os.path.join(dirsource, file),os.path.join(dirdestination, file)))
            self.process_file(os.path.join(dirsource, file), os.path.join(dirdestination, file+'.processed'))

    def stop_accelerator(self):
        # create an instance of the API class               
        api_instance = swagger_client.StopApi(api_client=self.api_configuration.api_client)
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
    def __init__(self, provider, client_id, secret_id, instance_id=None, sshKey=None,  
                region=None, instanceType=None, role=None, securityGroup=None, instance_url=None):
        self.provider = provider
        self.client_id = client_id
        self.secret_id = secret_id
        self.instance_id = instance_id
        self.sshKey = sshKey
        self.region = region
        self.instanceType = instanceType
        self.role = role
        self.securityGroup = securityGroup
        self.instance_url = instance_url
        
    def get_public_ip(self):
        try :
            r = requests.get('http://ipinfo.io/ip')
            logger.debug( "Public IP  answer : "+str(r.text))
            r.raise_for_status()
            if r.status_code == 200 :
              return r.text.strip()+"/32"
            return "0.0.0.0/0"
        except:
            logger.exception("Caught following exception:")
            raise Exception("Cannot get Accelize accelerator configuration")


#===================================
class AWSClass(CSPGenericClass):
#===================================  
    def __init__(self, *args, **kwargs):
        super(AWSClass, self).__init__("AWS", *args, **kwargs)
        
    def loadsession(self):
        try :
            import boto3
            self.session = boto3.session.Session(
                aws_access_key_id = self.client_id,
                aws_secret_access_key = self.secret_id,
                region_name = self.region
            )
            logger.info("Region: %s", self.session)
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
            logger.info("Create or check if KeyPair "+str(self.sshKey)+" exists.")
            try :
                ec2 = self.session.client('ec2')
                key_pair = ec2.describe_key_pairs( KeyNames=[self.sshKey])
                logger.info( "KeyPair on AWS named: "+str(key_pair['KeyPairs'][0]['KeyName'])+" already exists, nothing to do.")
                return True
            except Exception as e:
                logger.debug(str(e))
                logger.info("Create KeyPair %s", str(self.sshKey))
                ec2 = self.session.resource('ec2')
                key_pair = ec2.create_key_pair(KeyName=self.sshKey)
                with open(self.sshKey+".pem", "w") as text_file:
                    text_file.write(key_pair.key_material)
                os.chmod(self.sshKey+".pem", 0600)
                logger.debug("Key Content: %s", str(key_pair.key_material))
                logger.info("Key write in the current directory: %s.pem", self.sshKey)
                return True
        except:
            logger.exception("Failed to create SSHKey with exception:")
            return False

    def policy_csp(self, policy):
        try:
            logger.info("Create or check if policy "+str(policy)+" exists.")
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
            logger.info("Create or check if role %s exists", str(self.role))
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
            logger.info("Create or check if policy "+str(policy)+" is attached to role "+str(self.role)+" exists.")
            try :
                iam = self.session.client('iam')
                # Create a policy
                response =iam.attach_role_policy(PolicyArn=policy, RoleName=self.role)
                logger.debug("Policy: "+str(response))
                logger.info("Attach policy "+str(policy)+" to role "+str(self.role)+" done.")
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
            logger.info("Create or check if instance profile  "+str(instance_profile_name)+" exists.")
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
            logger.info("Create or Check if securitygroup  "+str(self.securityGroup)+" exists.")
            ec2 = self.session.client('ec2')
            public_ip = self.get_public_ip()
            try :
                response = ec2.describe_vpcs()
                vpc_id = response.get('Vpcs', [{}])[0].get('VpcId', '')
                logger.info( "Default VPC: "+str(vpc_id))
                response_create_security_group = ec2.create_security_group(GroupName=self.securityGroup,
                                         Description="Generated by script",
                                         VpcId=vpc_id)
                security_group_id = response_create_security_group['GroupId']
                logger.info( 'Security Group Created %s in vpc %s.' % (security_group_id, vpc_id))
            except Exception as e:
                logger.debug(str(e))
                logger.info( "Securitygroup on AWS named: :"+str(self.securityGroup)+" already exists.")
            my_sg = ec2.describe_security_groups( GroupNames=[self.securityGroup,],)
            try :
                my_sg = ec2.describe_security_groups( GroupNames=[self.securityGroup,],)
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
                logger.info( "Added in security group:"+self.securityGroup +" SSH and HTTP for IP:"+str(public_ip))
            except Exception as e:
                logger.debug(str(e))
                logger.info( "Right for IP "+str(public_ip)+" on AWS already exists, nothing to do.")
            return True
        except:
            logger.exception("Failed to create securityGroup with exception:")
            return False
            
    def wait_instance_ready(self):
        try:
            # Waiting for the instance to be running
            logger.info("Waiting for the instance to setup...")
            while True:
                instance = self.get_instance_csp()  # Absolutely mandatory to update the state of object (state is not updated automatically)
                if instance is None:
                    return None
                status = instance.state["Name"]
                logger.debug("Instance status: %s", status)
                if status == "running":
                    break
                time.sleep(5)
            logger.info("Instance %s!", status)
            # Waiting for the instance to respond to ping
            logger.info("Waiting for the instance to boot...")
            url = "http://%s" % instance.public_ip_address
            if not ping( url, 1, 72, 5 ): # 6 minutes timeout
                logger.error("Timed out while waiting CSP instance to boot.")
                return None
            logger.info("Instance booted!")
            return instance
        except:
            logger.exception("Caught following exception:")
            return None
            
    def get_instance_csp(self):
        ec2 = self.session.resource('ec2')
        instance = ec2.Instance(self.instance_id)
        try:
            logger.debug("Found an instance with ID %s in the following state: %s", self.instance_id, str(instance.state))
            return instance
        except:
            logger.error("Could not find an instance with ID %s", self.instance_id)
            return None
            
    def set_accelerator_requirements(self, accel_parameters):
        if self.region not in accel_parameters.keys():
            logger.error("Region '%s' is not supported. Available regions are: %s", self.region, ', '.join(accel_parameters.keys()))
            return False
        self.accelerator = accel_parameters['accelerator']
        accel_parameters_in_region = accel_parameters[self.region]
        self.template_instance = {'AGFI': accel_parameters_in_region['fpgaimage']}
        self.imageId = accel_parameters_in_region['image']
        self.instanceType = accel_parameters_in_region['instancetype']
        
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
                                            InstanceType=self.instanceType,
                                            KeyName=self.sshKey,
                                            SecurityGroups=[
                                                self.securityGroup,
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
            instance = instance[0]
            self.instance_id = instance.id
            logger.info("Created instance ID: %s", self.instance_id)
            return self.wait_instance_ready()
        except:
            logger.exception("Caught following exception:")
            return None

    def start_existing_instance_csp(self):
        try:
            instance = self.get_instance_csp()
            if instance is None:
                return None
            logger.info("Using instance ID: %s", self.instance_id)
            state = instance.state["Name"]
            if state == "stopped":
                response = instance.start()
                logger.debug("start response: %s", str(response))
            elif state != "running":
                logger.error("Instance ID %s cannot be started because it is not in a valid state (%s).", self.instance_id, state)
                return None
            if not self.wait_instance_ready():
                raise Exception("Error occurred when waiting instance to be ready.")
            return instance
        except:
            logger.exception("Caught following exception:")
            return None
            
    def start_instance_csp(self):
        if self.instance_id is None:
            instance = self.start_new_instance_csp()
        else:
            instance = self.start_existing_instance_csp()
        if instance is None:
            return False
        logger.info("Private IP: %s", instance.private_ip_address)
        logger.info("Public IP: %s", instance.public_ip_address)
        self.instance_url = "http://%s" % instance.public_ip_address
        logger.info("Your instance is now up and running")
        return True

    def stop_instance_csp(self, terminate=True):
        try:
            instance = self.get_instance_csp()
            if instance is None:
                return False
            if terminate:
                logger.info("Terminating instance ID %s", self.instance_id)
                response = instance.terminate()
            else:
                logger.info("Stopping instance ID %s", self.instance_id)
                response = instance.stop()
            logger.debug("Stop response: %s", str(response))
            return True
        except:
            logger.exception("Caught following exception:")
            return False


#===================================
class OVHClass(CSPGenericClass):
#===================================
    def __init__(self, *args, **kwargs):
        super(OVHClass, self).__init__("OVH", *args, **kwargs)
                
    
#===================================
class CSPClassFactory(object):
#===================================
    def __new__(self, provider, *args, **kwargs):
        if provider == 'AWS':
            return AWSClass(*args, **kwargs)
        elif provider == 'OVH':
            return OVHClass(*args, **kwargs)
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
                csp_secret_id=None, ssh_key=None, instance_type=None, security_group=None,
                role=None, instance_id=None, ip_address=None):
        global config
        if config_file is None:
            config_file = DEFAULT_CONFIG_FILE
        if not os.path.isfile(config_file):
            raise Exception("Could not find configuration file: %s" % config_file)
        logger.debug("Using configuration file: %s", config_file)
        config.read(config_file)
        self.accelerator = accelerator
        self.provider = getVal(provider, "csp", "provider")
        instance_id = getVal(instance_id, "csp", "instance_id")
        ip_address = getVal(ip_address, "csp", "ip_address")
        if ip_address:
            instance_url = "http://" + ip_address
        else:
            instance_url = None
        region = getVal(region, "csp", "region")
        xlz_client_id = getVal(xlz_client_id, "accelize", "client_id")
        xlz_secret_id = getVal(xlz_secret_id, "accelize", "secret_id")
        csp_client_id = getVal(csp_client_id, "csp", "client_id")
        csp_secret_id = getVal(csp_secret_id, "csp", "secret_id")
        ssh_key = getVal(ssh_key, "csp", "sshKey")
        instance_type = getVal(instance_type, "csp", "instanceType")
        security_group = getVal(security_group, "csp", "securityGroup")
        role = getVal(role, "csp", "role")
        self.configResult = None
        self.processResult = None
        self.stopResult = None
        # Create CSP object
        self.csp_instance = CSPClassFactory(provider=self.provider, client_id=csp_client_id, secret_id=csp_secret_id,  
                sshKey=ssh_key, region=region, instanceType=instance_type, securityGroup=security_group,
                role=role, instance_id=instance_id, instance_url=instance_url)
        self.sign_handler = SignalHandlerAccelerator(self.csp_instance)
        # Create Accelerator object
        self.accelerator_instance = GenericAcceleratorClass(accelerator, client_id=xlz_client_id, secret_id=xlz_secret_id)
                        
    def __del__(self):
        self.sign_handler.signal_handler_accelerator(False)
        
    def getConfigResult(self):
        return self.configResult
        
    def getProcessResult(self):
        return self.processResult
        
    def getStopResult(self):
        return self.stopResult

    # Start a new instance or use a running instance
    def start_instance(self, stop_mode=None):
        stop_mode = getVal(stop_mode, "csp", "stop_mode")
        if stop_mode is None:
            stop_mode = TERM
        self.sign_handler.set_stop_mode(stop_mode)
        # Checking if credentials are valid otherwise no sense to continue
        if not self.accelerator_instance.check_accelize_credential():
            return False
        if self.csp_instance.instance_url is None:
            if not self.csp_instance.check_csp_credential():
                return False
            accel_requirements = self.accelerator_instance.get_accelerator_requirements(self.provider)
            if accel_requirements is None:
                return False
            self.csp_instance.set_accelerator_requirements(accel_requirements)
            if self.csp_instance.instance_id is None:
                if not self.csp_instance.create_instance_csp():
                    return False
            if not self.csp_instance.start_instance_csp():
                return False
            self.sign_handler.append_instance(self.csp_instance.instance_id)
        self.accelerator_instance.setUrl(self.csp_instance.instance_url)
        logger.info("Accelerator URL: %s", self.csp_instance.instance_url)
        # If possible use the last accelerator configuration (it can still be overwritten later)
        self.accelerator_instance.use_last_configuration()             
        return True
        
    def getInfoFromResult(self, result):
        if 'app' not in result.keys():
            return -1, "No result returned!"
        retcode = result['app']['status']
        msg = result['app']['msg']
        return (retcode, msg)
        
    def configure_accelerator(self, datafile=None, accelerator_parameters=None, template_instance=None):
        try :
            logger.debug("Starting accelerator '%s' on instance ID %s", self.accelerator_instance.accelerator, self.csp_instance.instance_id)
            if not ping(self.accelerator_instance.getUrl(), 10):
                return False
            if template_instance is not None:
                self.csp_instance.template_instance = template_instance
                logger.warn("Overwrite factory requirements with custom configuration:\n%s", prettyDict(template_instance)) 
            logger.debug("template_instance: %s", str(self.csp_instance.template_instance))
            envserver = { "client_id":self.accelerator_instance.client_id, "client_secret":self.accelerator_instance.secret_id }
            envserver.update(self.csp_instance.template_instance)
            self.configResult = self.accelerator_instance.configure_accelerator(envserver=envserver, accelerator_parameters=accelerator_parameters, datafile=datafile)
            ret, msg = self.getInfoFromResult(self.configResult)
            if ret:
                logger.error("Configuration of accelerator failed: %s", msg)
                return False
            logger.info("Configuration of accelerator is complete")
            return True
        except Exception as e:
            logger.exception("Caught following exception:")
            return False

    def start(self, stop_mode=TERM, datafile=None, accelerator_parameters=None, template_instance=None):
        logger.debug("Starting accelerator server '%s' on '%s'", self.accelerator, self.provider)
        # Start a new instance or use a running instance
        if not self.start_instance(stop_mode):
            return False            
        # Configure accelerator if needed
        if self.accelerator_instance.accelerator_configuration_url is None:
            return self.configure_accelerator(datafile, accelerator_parameters, template_instance)
        else:
            self.configResult = {'app': {'status':0, 'msg':"Already loaded with configuration: %s" % self.accelerator_instance.accelerator_configuration_url}}
        return True

    def process(self, file_in, file_out, process_parameter=None):
        logger.debug("Starting a processing job: in=%s, out=%s", file_in, file_out)
        try :
            accel_url = self.accelerator_instance.getUrl()
            logger.debug("Accelerator URL: %s", accel_url)
            if not ping(accel_url, 10):
                return False
            self.processResult = self.accelerator_instance.process_file(file_in=file_in, file_out=file_out, accelerator_parameters=process_parameter)
            ret, msg = self.getInfoFromResult(self.processResult)
            if ret:
                return False
            logger.info("Processing on accelerator is complete")
            return True
        except Exception as e:            
            logger.exception("Caught following exception:")
            return False

    def stop_accelerator(self):
        logger.debug("Stopping accelerator '%s' on instance ID %s", self.accelerator, self.csp_instance.instance_id)
        try :
            if not ping(self.accelerator_instance.getUrl(), 10):
                return False
            self.stopResult = self.accelerator_instance.stop_accelerator()
            ret, msg = self.getInfoFromResult(self.stopResult)
            if ret:
                logger.error("Stopping accelerator failed: %s", msg)
                return False
            logger.info("Stopping accelerator is complete")
            return True
        except Exception as e :
            logger.exception("Caught following exception:")
            return False
            
    def stop_instance(self, stop_mode=TERM, blocking=False):
        logger.debug("Stopping instance (ID: %s) on '%s'", self.csp_instance.instance_id, self.provider)
        try:
            self.stop_accelerator()
            if stop_mode == KEEP:
                self.sign_handler.set_stop_mode(stop_mode)
                return True
            terminate = True if stop_mode == TERM else False
            self.csp_instance.stop_instance_csp(terminate)
            self.sign_handler.remove_instance(self.csp_instance.instance.id)
            return True
        except:
            logger.exception("Caught following exception:")
            return False

    def stop(self, stop_mode=TERM):
        if self.stop_instance(stop_mode):
            return False
        return True
        
    def getInfo(self):
        d = dict()
        d['publicIP'] = self.csp_instance.instance.public_ip_address
        d['privateIP'] = self.csp_instance.instance.private_ip_address
        d['configuration_url'] = self.accelerator_instance.accelerator_configuration_url
        return d
        

################################# Accelerator Class [end] ########################################################
