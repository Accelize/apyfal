import time
import signal
import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir =  os.path.abspath(os.path.join(os.path.join(os.path.join(os.path.join(currentdir, os.pardir), os.pardir),'REST_API'),'python'))
sys.path.insert(0,parentdir)
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint
import shutil, urllib3, os
from multiprocessing import Pool
import requests
import json
import logging
import socket
import ConfigParser
import os.path
from urllib2 import urlopen, URLError, HTTPError
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
config = ConfigParser.ConfigParser(allow_no_value=True)
#Should be present in the execution folder
config.read("accelerator.conf" )

class SignalHandlerAccelerator(object):
    '''Signal handler for Instances'''

    def __init__(self, csp_instance):
        self.instances = []
        self.csp_instance =csp_instance
        self.set_signals()
        self.stop_instances=False
        self.terminate = True
    def append_ip_address(self, ip, instance_id):
        self.instances.append({"ip":ip,"instance_id":instance_id})
    def definestop_instances(self,stop_instance):
        self.stop_instances =stop_instance
    def defineterminate_instances(self,terminate):
        self.terminate =terminate
    def set_signals(self):
        '''Set a list of interrupt signals to be handled asynchronously'''
        signal.signal(signal.SIGTERM, self.signal_handler_accelerator)
        signal.signal(signal.SIGINT, self.signal_handler_accelerator)
        signal.signal(signal.SIGQUIT, self.signal_handler_accelerator)
    def signal_handler_accelerator(self, _signo="", _stack_frame=""):
        '''Try to stop all instances running or inform user'''
        logger.warn( "signal_handler_accelerator")
        if self.stop_instances:
            for instance in self.instances:
               logger.info("=>Stopping instance with Public IP address: " +instance["ip"]+ " instance_id:"+instance["instance_id"])
               self.csp_instance.stop_instance_csp(instance["instance_id"],self.terminate)
        elif self.instances:
            iplist =""
            for instance in self.instances:
               iplist+=instance["ip"]+ " instance_id:"+instance["instance_id"]+" "
            logger.warn( "=>###########################################################")
            logger.warn( "=>##Warning : instances are still running with public IPs :"+ str(iplist))
            logger.warn( "=>######Make sure you will stop them manually later.########")
            logger.warn( "=>###########################################################")

        logger.info("=>Accelerator API Closed properly")
        sys.exit(0)
        

################################# Rest API material [begin]########################################################
class GenericAcceleratorClass(object):
    '''############################################
    #####  EndUser API based on the openAPI Accelize accelerator
    #####  Objective of this API it to remove complex user actions
    ############################################
    '''
    #Variable Shared
    accelerator_configuration_url=config.get("process", "url_configuration")
    accelerator_parameters_configuration=eval(config.get("configuration", "parameters"))
    accelerator_parameters_process=eval(config.get("process", "parameters"))

    api_configuration = swagger_client.Configuration()

    def __init__(self,url='http://localhost', accelerator_configuration_url=""):
        #A regular API has fixed url. In our case we want to change it dynamically.
        self.api_configuration = swagger_client.Configuration()
        self.api_configuration.host = url

        #The last configuration URL should be keep in order to not request it to user.
        self.accelerator_configuration_url=accelerator_configuration_url

        #envserver = json env
    def configure_accelerator(self,envserver,accelerator_parameters="",datafile = "") :
        #######################################################################################
        ############     Create an Accelerator configuration
        #######################################################################################
        try:
            # /v1.0/configuration/
            # create an instance of the API class

            api_instance = swagger_client.ConfigurationApi(api_client=self.api_configuration.api_client)

            if accelerator_parameters == "":
                logger.debug( "=>Using default configuration")
                accelerator_parameters=self.accelerator_parameters_configuration

            parameters = {"env":envserver,"app":accelerator_parameters}
            logger.debug( "configuration_create:"+str(json.dumps(parameters))+" datafile: "+datafile)
            api_response = api_instance.configuration_create(parameters=json.dumps(parameters), datafile=datafile)
            logger.debug( "configuration_create api_response:"+str(api_response))
            id = api_response.id

            self.accelerator_configuration_url = api_response.url


            dictparameters = eval(api_response.parametersresult)
            dictparameters['url']= api_response.url
            logger.info( "=>status:"+str(dictparameters['app']['status']) )
            logger.info( "=>msg:\n"+dictparameters['app']['msg'] )
            api_response_read = api_instance.configuration_read(id)
            if api_response_read.inerror :
                raise ValueError('Cannot start the confirguration '+str(api_response_read.url))
            return dictparameters
        except ApiException as e:
            logger.error(  "Exception when calling ConfigurationApi->configuration_create: %s\n" % e)
            return {'error':str(e)}
    def process(self,file_in="",file_out="",accelerator_parameters="") :
        # create an instance of the API class
        api_instance = swagger_client.ProcessApi(api_client=self.api_configuration.api_client)
        if accelerator_parameters == "":
            logger.debug( "=>Using default configuration")
            accelerator_parameters=self.accelerator_parameters_process
        configuration =self.accelerator_configuration_url
        datafile = file_in # file | If needed, file to be processed by the accelerator. (optional)
        try:
            try: # Bypass REST API because upload issue with big file using python https://bugs.python.org/issue8450
                import pycurl
                from StringIO import StringIO
                logger.debug( "pycurl process:"+str(configuration)+" datafile:"+datafile )
                storage = StringIO()
                c = pycurl.Curl()
                c.setopt(c.WRITEFUNCTION, storage.write)
                c.setopt(c.URL, self.api_configuration.host+"/v1.0/process/")
                c.setopt(c.POST, 1)
                c.setopt(c.HTTPPOST, [("datafile", (c.FORM_FILE, file_in)),
                                    ("parameters", json.dumps(accelerator_parameters)),
                                    ("configuration", configuration)])
                c.setopt(c.HTTPHEADER, ['Content-Type: multipart/form-data'])
                #c.setopt(c.VERBOSE, 1)
                c.perform()
                c.close()
                content = storage.getvalue()
                logger.debug( "pycurl process:"+str(content) )
                r2 = json.loads(content)
                #api_client = Struct(**r2)
                id = r2['id']
                processed = r2['processed']
            except ImportError:
                logger.debug( "process_create process:"+str(configuration)+" datafile:"+datafile )
                api_response = api_instance.process_create(configuration, parameters=json.dumps(accelerator_parameters), datafile=datafile)
                id = api_response.id
                processed = api_response.processed

            while processed <> True :
                api_response = api_instance.process_read(id)
                processed = api_response.processed
                if api_response.inerror :
                    raise ValueError('Cannot start the process '+str(api_response.parametersresult))
            http = urllib3.PoolManager()
            with http.request('GET', api_response.datafileresult, preload_content=False) as r, open(file_out, 'wb') as out_file:
                shutil.copyfileobj(r, out_file)
            logger.debug( "process_delete api_response: "+str(id) )
            api_response_delete = api_instance.process_delete(id)
            dictparameters = eval(api_response.parametersresult)
            logger.info(  "=>status:"+str(dictparameters['app']['status']))
            logger.info(  "=>msg:\n"+dictparameters['app']['msg'])
            return dictparameters
        except ApiException as e:
            logger.error(  "Exception when calling ProcessApi->process_create: %s\n" % e)
            return {'error':str(e)}
    def process_directory(self,dirsource="",dirdestination="",parameters='{}',processes=4) :
        configuration = self.accelerator_configuration_url
        #pool = Pool(processes=processes)              # start 4 worker processes
        for file in os.listdir(dirsource):
            #pool.apply_async(process, (os.path.join(dirsource, file),os.path.join(dirdestination, file),configuration,parameters))
            #pool.apply(self.process, (os.path.join(dirsource, file),os.path.join(dirdestination, file)))
            self.process(os.path.join(dirsource, file),os.path.join(dirdestination, file+'.processed'))

    def stop_accelerator(self):
        # create an instance of the API class
        api_instance = swagger_client.StopApi(api_client=self.api_configuration.api_client)
        try:
            # /v1.0/stop
            return api_instance.stop_list()
        except ApiException as e:
            print "Exception when calling StopApi->stop_list: %s\n" % e
            return {'error':str(e)}
################################# Rest API material [end]########################################################
################################# CSP material [begin]########################################################
class CSPGenericClass(object):

    def __init__(self,provider=config.get("csp", "provider"),role=config.get("csp", "role"), client_id_csp="", secret_id_csp="",region=config.get("csp", "region"),sshKey=config.get("csp", "sshKey"),instanceType="",securityGroup=config.get("csp", "securityGroup")):
        self.provider = provider
        self.client_id_csp=client_id_csp
        self.secret_id_csp=secret_id_csp
        self.region= region
        self.sshKey=sshKey
        self.instanceType=instanceType
        self.securityGroup=securityGroup
        self.role=role
    def get_accelize_configuration(self,accelerator):
        try :
            r = requests.post('https://master.metering.accelize.com/o/token/',data={"grant_type":"client_credentials"} , auth=(self.client_id, self.client_secret))
            logger.debug( "Accelize token answer : "+str(r.text))
            r.raise_for_status()
            if r.status_code == 200 :
               #call WS
               answer_token = json.loads(r.text)
               headers = {"Authorization": "Bearer "+str(answer_token['access_token']),"Content-Type":"application/json","Accept":"application/vnd.accelize.v1+json"}
               r = requests.get('https://master.metering.accelize.com/auth/getlastcspconfiguration/',headers=headers)
               logger.debug( "Accelize config answer : "+str(r.text)+ " status :"+str(r.status_code))
               r.raise_for_status()
               try :
                    configuration_accelerator = json.loads(r.text)
                    
                    return configuration_accelerator[self.provider][accelerator][self.region]
               except Exception as e:
                    raise Exception("Not able to find a configuration for provider:"+self.provider+" accelerator: "+accelerator+" region"+self.region+ " Error:"+str(e))
            
        except Exception as e:
            raise Exception("Cannot get Accelize accelerator configuration : "+str(e))

        
    def stop_instance_csp(self,instance_id):
        logger.warn( "Stop instance with id "+str(instance_id))
        pass
    def start_instance_csp(self,parametercsp):
        pass

    def credential_check_csp(self):
        pass
    def wait_server(self,url):
        '''
            Checking if an HTTP is up and running.
        '''
        socket.setdefaulttimeout( 1 )  # timeout in seconds
        done=False
        count=0
        logger.info("Wait for the server to wake up")
        while not done and count<120 :
            logger.debug("Loop for the server to wake up")
            count=count+1
            try :
                response = urlopen( url )
                done=True
                break;
            except Exception as e:
                pass
            time.sleep(5)
        logger.info("Server ruuning:"+str(done))
        socket.setdefaulttimeout( 900 )  # timeout in seconds
    def check_accelize_credential(self,client_id="",client_secret=""):
        try :
            r = requests.post('https://master.metering.accelize.com/o/token/',data={"grant_type":"client_credentials"} , auth=(client_id, client_secret))
            if r.status_code != 200 :
                raise Exception("Accelize authentication failed: "+str(r.text))
            self.client_id=client_id
            self.client_secret=client_secret
        except Exception as e:
            raise Exception("Accelize authentication failed: "+str(e))

        return "Accelize authentication successful"

class AWSClass(CSPGenericClass):
    def configuration_csp(self,accelerator):
        #call webservice
        self.csp_parameter= self.get_accelize_configuration(accelerator)
        self.template_instance = self.get_csp_format(self.csp_parameter)
        self.accelerator = accelerator
        self.credential_check_csp()
        self.ssh_key_csp()
        policy_arn = self.policy_csp('AccelizePolicy')
        self.role_csp()
        self.instance_profile_csp()
        self.attach_role_policy_csp(policy_arn)
        self.security_group_csp()
        return self.start_instance_csp(),self.template_instance
    def get_csp_format(self,csp_parameter):
        self.template_instance = {'AGFI':csp_parameter["fpgaimage"]}
        self.imageId = csp_parameter["image"]
        self.agfi= csp_parameter["fpgaimage"] 
        
        self.instanceType = csp_parameter["instancetype"]
        return self.template_instance
    def loadsession (self):
        try :
            import boto3
            self.session = boto3.session.Session(
                aws_access_key_id=self.client_id_csp,
                aws_secret_access_key=self.secret_id_csp,
                region_name=self.region
            )
        except Exception as e:
            raise Exception("Cannot load boto module : "+str(e))
    def credential_check_csp(self):
        try :
            self.loadsession()
            ec2 = self.session.client('ec2')
            response = ec2.describe_key_pairs()
            
        except Exception as e:
            raise Exception("CSP authentication failed: "+str(e))
    def ssh_key_csp(self):
        try:
            logger.info("Create or check if KeyPair "+str(self.sshKey)+" exists.")
            try :
                ec2 = self.session.client('ec2')
                key_pair = ec2.describe_key_pairs( KeyNames=[self.sshKey])
                logger.info( "KeyPair exist on CSP: "+str(key_pair['KeyPairs'][0]['KeyName'])+ ", nothing to do.")
            except Exception as e:
                logger.debug(str(e))
                logger.info("Create KeyPair "+str(self.sshKey)+".")
                ec2 = self.session.resource('ec2')
                key_pair = ec2.create_key_pair(KeyName=self.sshKey)
                with open(self.sshKey+".pem", "w") as text_file:
                    text_file.write(key_pair.key_material)
                os.chmod(self.sshKey+".pem", 0600)
                logger.debug( "Key Content: "+str(key_pair.key_material))
                logger.info( "Key write in the current directory: "+self.sshKey+".pem")
        except Exception as e:
            raise Exception("Failed to create SSHKey: "+str(e))
    def policy_csp(self,policy):
        try:
            logger.info("Create or check if policy "+str(policy)+" exists.")
            try :
                iam = self.session.client('iam')
                # Create a policy 
                my_managed_policy = {    "Version": "2012-10-17",
                                        "Statement": [
                                                    {
                                                    "Sid": "AllowFpgaCommands",
                                                    "Effect": "Allow",
                                                    "Action": [
                                                        "ec2:AssociateFpgaImage",
                                                        "ec2:DisassociateFpgaImage",
                                                        "ec2:DescribeFpgaImages"
                                                            ],
                                                    "Resource": [                "*"            ]        }    ]
                                    }
                response = iam.create_policy(
                            PolicyName=policy,
                            PolicyDocument=json.dumps(my_managed_policy)
                )
                logger.debug( "Policy: "+str(response))
            except Exception as e:
                logger.debug(str(e))
                iam = self.session.resource('iam')
                logger.debug( "Policy:"+str(policy)+" already exists.")

            iam = self.session.client('iam')
            response = iam.list_policies(
                Scope='Local',
                OnlyAttached=False,
                MaxItems=100
                )
            for policyitem in response['Policies']:
                if policyitem['PolicyName'] == policy :
                    return policyitem['Arn']
                    break
            return None
            logger.debug( "Policy ARN:"+str(response)+" already exists.")
        except Exception as e:
            raise Exception("Failed to create policy: "+str(e))
    def role_csp(self):
        try :
            logger.info("Create or check if role "+str(self.role)+" exists.")
            try :
                iam = self.session.resource('iam')
                role = iam.create_role(RoleName=self.role,
                AssumeRolePolicyDocument='{  "Version": "2012-10-17",  "Statement": {    "Effect": "Allow",    "Principal": {"Service": "ec2.amazonaws.com"},    "Action": "sts:AssumeRole"  }}',
                Description='Created automaticly'
                )
                logger.debug( "role: "+str(role))
            except Exception as e:
                logger.debug(str(e))
                logger.info( "Role: "+str(self.role)+" already exists.")
            iam = self.session.client('iam')
            response = iam.get_role(
                                RoleName=self.role
                            )
            logger.debug( "Policy ARN:"+str(response['Role']['Arn'])+" already exists.")
            return response['Role']['Arn']
        except Exception as e:
            raise Exception("Failed to create role: "+str(e))
    def attach_role_policy_csp(self,policy):
        try:
            logger.info("Attach policy "+str(policy)+" to role "+str(self.role)+" exists.")
            try :
                iam = self.session.client('iam')
                # Create a policy 
                response =iam.attach_role_policy(
                                        PolicyArn=policy,
                                        RoleName=self.role
                                    )
                logger.debug( "Policy: "+str(response))
            except Exception as e:
                logger.debug(str(e))
                logger.info( "Attach: "+str(policy)+" and role: "+str(self.role)+" already exists.")
        except Exception as e:
            raise Exception("Failed to attach policy to role: "+str(e))
    def instance_profile_csp(self):
        try:
            instance_profile_name ='AccelizeLoadFPGA'
            logger.info("Create or check if instance profile  "+str(instance_profile_name)+" exists.")
            try :
                iam = self.session.client('iam')
                instance_profile = iam.create_instance_profile(
                                        InstanceProfileName=instance_profile_name
                                    )
                instance_profile.add_role(
                                    RoleName=self.role
                                )
                logger.debug( "Instance profile : "+str(instance_profile))
            except Exception as e:
                logger.debug(str(e))
                logger.info( "instance profile name: "+str(instance_profile_name)+" already exists.")
        except Exception as e:
            raise Exception("Failed to attach policy to role: "+str(e))
    def security_group_csp(self):
        try:
            logger.info("Create or Check if securitygroup  "+str(self.securityGroup)+" exists.")
            try :
                ec2 = self.session.client('ec2')
                
                response = ec2.describe_vpcs()
                vpc_id = response.get('Vpcs', [{}])[0].get('VpcId', '')
                logger.info( "Default VPC: "+str(vpc_id))
                response_create_security_group = ec2.create_security_group(GroupName=self.securityGroup,
                                         Description="Generated by script",
                                         VpcId=vpc_id)
                security_group_id = response_create_security_group['GroupId']
                logger.info( 'Security Group Created %s in vpc %s.' % (security_group_id, vpc_id))
                data = ec2.authorize_security_group_ingress(
                                                    GroupId=security_group_id,
                                                    IpPermissions=[
                                                        {'IpProtocol': 'tcp',
                                                         'FromPort': 80,
                                                         'ToPort': 80,
                                                         'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
                                                        {'IpProtocol': 'tcp',
                                                         'FromPort': 22,
                                                         'ToPort': 22,
                                                         'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}
                                                    ])
                logger.debug( "Successfully Set "+str(data))
            except Exception as e:
                logger.debug( "securitygroup : "+str(self.securityGroup)+" already exists."+str(e))
        except Exception as e:
            raise Exception("Failed to create securityGroup: "+str(e))
    def start_instance_csp(self):
        #try :
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
                                                            'Value': "Accelize accelerator "+str(self.accelerator)
                                                        },
                                                    ]
                                                },
                                            ],
                                            MinCount=1, MaxCount=1
                                        )
            logger.debug( str(instance))
            logger.info( "Instance ID :"+str(instance[0].id)
                                +" Private IP :"+str(instance[0].private_ip_address))
            while instance[0].state["Name"] =="pending":
                time.sleep(3)
                instance[0] =  ec2.Instance(instance[0].id)
                logger.debug("Instance status: "+str(instance[0].state["Name"]))
            logger.info( "Instance Status :"+str(instance[0].state["Name"])+" Public IP :"+str(instance[0].public_ip_address))

            #public_ip_address state private_ip_address
            logger.debug( str(instance))
            self.wait_server("http://"+str(instance[0].public_ip_address) )
            return instance[0]
        #except Exception as e:
        #    raise Exception("Failed to start instance : "+str(e))
    def stop_instance_csp(self,instance_id,terminate =True):
        logger.warn( "Stop instance with id: "+str(instance_id))
        ec2 = self.session.resource('ec2')
        
        instance =  ec2.Instance(instance_id)
        logger.debug( "Stop instance: "+str(instance))
        if terminate:
            response = instance.terminate()
        else:
            response = instance.stop()
        logger.debug( "Stop response: "+str(response))

class OVHClass(CSPGenericClass):
    def  credential_check_csp(self,client_id_csp,secret_id_csp):
        pass
    def start_instance_csp(self,parametercsp,client_id_csp,secret_id_csp):
        pass

class CSPClassFactory(object):
    def __new__(self, provider, **kwargs):
        if provider == 'AWS':
            return AWSClass(provider, **kwargs)
        elif provider == 'OVH':
            return OVHClass(provider, **kwargs)
        else:
            raise ValueError('Cannot initate a CSP class with this provider:'+str(provider))
################################# CSP material [end] ########################################################


################################# Accelerator Class [begin] ########################################################
class AcceleratorClass(object):
    '''
    This Call is hidden complexity of using GenericAcceleratorClass and CSPGenericClass

    '''
    provider=""
    instance_id=""
    url_instance=""
    client_id=""
    client_secret=""
    csp_instance=CSPGenericClass()
    accelerator_instance= GenericAcceleratorClass()
    def __init__(self,provider, instance_id="",region=config.get("csp", "region"),client_id=config.get("accelize", "client_id"),client_secret=config.get("accelize", "secret_id"),stop_instance=False,client_id_csp=config.get("csp", "client_id"),secret_id_csp=config.get("csp", "secret_id"),sshKey=config.get("csp", "sshKey"),instanceType=config.get("csp", "instanceType"),securityGroup=config.get("csp", "securityGroup"),role=config.get("csp", "role")):
        self.provider = provider
        self.instance_id = instance_id
        self.region = region
        self.client_id=client_id
        self.client_secret=client_secret
        self.stop_instance=stop_instance
        #load from file is exist
        self.configuration_envserver =''
        ##Checking If Credential are valid otherwise no sense to continue
        self.csp_instance = CSPClassFactory(region=region,provider=provider,client_id_csp=client_id_csp,secret_id_csp=secret_id_csp,sshKey=sshKey,instanceType=instanceType,securityGroup=securityGroup,role=role)
        self.sign_handler = SignalHandlerAccelerator(self.csp_instance)
        self.sign_handler.definestop_instances(stop_instance)
        self.csp_instance.check_accelize_credential(client_id=client_id,client_secret=client_secret)


    def __del__(self):
        self.sign_handler.signal_handler_accelerator()
    def ping_server(self):
        '''
            Checking if an HTTP is up and running.
        '''
        socket.setdefaulttimeout( 10 )  # timeout in seconds
        try :
            response = urlopen( self.url_instance )
        except Exception as e:
            logger.error("Cannot reach url :"+str(self.url_instance)+ " error:"+str(e))
            raise ValueError("Cannot reach url :"+str(self.url_instance)+ " error:"+str(e))
        socket.setdefaulttimeout( 900 )  # timeout in seconds


    def start_accelerator(self,start_instance=True, datafile="",template_instance="",ip_address=config.get("configuration", "ip_address"),accelerator_parameters="",accelerator="") :
        #try :
            if start_instance and  accelerator<>"":
                logger.debug("Starting an Instance")
                instance, template_instance=self.csp_instance.configuration_csp(accelerator=accelerator)
                instance_id = instance.id
                ip_address = instance.public_ip_address
                self.sign_handler.append_ip_address(ip_address,instance_id)
            elif not start_instance:
                if ip_address=="":
                    raise ValueError('You choose reuse an existing instance, please provide ip_address and template_instance value')
                if template_instance=="" and  accelerator<>"":
                    csp_parameter = self.csp_instance.get_accelize_configuration(accelerator=accelerator)
                    template_instance = self.csp_instance.get_csp_format(csp_parameter)
                    logger.debug(  "template_instance: "+str(template_instance))
            else :
                ValueError('A parameter is missing, please check the documentation.')
            
            self.url_instance ='http://'+str(ip_address)
            logger.info(  "=>Accelerator URL: "+self.url_instance)
            self.accelerator_instance = GenericAcceleratorClass(url=self.url_instance)
            envserver={"client_id":self.client_id,"client_secret":self.client_secret}
            envserver.update(template_instance)
            self.ping_server()
            logger.info(  "=>Starting internal configuration "+self.provider+" region: "+self.region)
            return self.accelerator_instance.configure_accelerator(envserver=envserver,accelerator_parameters=accelerator_parameters,datafile = datafile)

        #except Exception as e :
        #    #Return Issue
        #    logger.error(  str(e))
        #    return {'error':str(e)}
    def process(self,file_in="",file_out="",process_parameter="",url_configuration=""):
        try :

            if url_configuration<>"":
                logger.debug("Using a configuration generated outside the Class url:"+str(url_configuration))
                url_instance = url_configuration.split('/v1.0/', 1)[0]
                logger.debug("So URL instance is url_instance:"+str(url_instance))
                self.url_instance = url_instance
                self.accelerator_instance = GenericAcceleratorClass(url=url_instance)
                self.accelerator_instance.accelerator_configuration_url = url_configuration
            self.ping_server()
            logger.debug("Using URL configuration:"+str(self.accelerator_instance.accelerator_configuration_url))
            return self.accelerator_instance.process(file_in=file_in,file_out=file_out,accelerator_parameters=process_parameter)
        except Exception as e :
            #Return Issue
            logger.error(  str(e))
            return {'error':str(e)}

    def stop_accelerator(self):
        try :
            self.ping_server()
            data = self.accelerator_instance.stop_accelerator()
            return data
        except Exception as e :
            #Return Issue
            logger.error(  str(e))
            return {'error':str(e)}

################################# Accelerator Class [end] ########################################################

