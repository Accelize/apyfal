import json
import os
import time
import copy
from acceleratorAPI.utilities import pretty_dict, check_url
from acceleratorAPI import logger
from acceleratorAPI.csp import CSPGenericClass as _CSPGenericClass
import boto3
import openstack


class AWSClass(_CSPGenericClass):

    def __init__(self, provider, config_parser, **kwargs):
        self.provider = provider
        role = _CSPGenericClass.get_from_args('role', **kwargs)
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
        try:
            self.session = boto3.session.Session(
                aws_access_key_id=self.client_id,
                aws_secret_access_key=self.secret_id,
                region_name=self.region
            )
        except Exception:
            logger.exception("Caught following exception:")
            raise Exception("Could not authenticate to your %s account", self.provider)

    def check_csp_credential(self):
        try:
            ec2 = self.session.client('ec2')
            response = ec2.describe_key_pairs()
            logger.debug("Response of 'describe_key_pairs': %s", str(response))
            return True
        except Exception:
            logger.exception("Failed to authenticate with your CSP access key.")
            return False

    def ssh_key_csp(self):
        try:
            logger.debug("Create or check if KeyPair " + str(self.ssh_key) + " exists.")
            try:
                ec2 = self.session.client('ec2')
                key_pair = ec2.describe_key_pairs(KeyNames=[self.ssh_key])
                logger.info("KeyPair '%s' is already existing on %s.", str(key_pair['KeyPairs'][0]['KeyName']),
                            self.provider)
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
        except Exception:
            logger.exception("Failed to create SSH Key with exception:")
            return False

    def policy_csp(self, policy):
        try:
            logger.debug("Create or check if policy " + str(policy) + " exists.")
            try:
                iam = self.session.client('iam')
                # Create a policy
                my_managed_policy = {"Version": "2012-10-17",
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
                response = iam.create_policy(PolicyName=policy, PolicyDocument=json.dumps(my_managed_policy))
                logger.debug("Policy: %s", str(response))
                logger.info("Policy: %s created", str(instance_profile_name))
            except Exception as e:
                logger.debug(str(e))
                logger.info("Policy on AWS named: %s already exists, nothing to do.", str(policy))

            iam = self.session.client('iam')
            response = iam.list_policies(Scope='Local', OnlyAttached=False, MaxItems=100)
            for policyitem in response['Policies']:
                if policyitem['PolicyName'] == policy:
                    return policyitem['Arn']
            return None
        except Exception:
            logger.exception("Failed to create policy with exception:")
            return None

    def role_csp(self):
        try:
            logger.debug("Create or check if role %s exists", str(self.role))
            try:
                iam = self.session.resource('iam')
                role = iam.create_role(
                    RoleName=self.role,
                    AssumeRolePolicyDocument=
                    '{"Version": "2012-10-17", "Statement": '
                    '{"Effect": "Allow", "Principal": {"Service": "ec2.amazonaws.com"}, "Action": "sts:AssumeRole"}}',
                    Description='Created automaticly'
                )
                logger.debug("role: %s", str(role))
            except Exception as e:
                logger.debug(str(e))
                logger.info("Role on AWS named: %s already exists, nothing to do.", str(self.role))
            iam = self.session.client('iam')
            response = iam.get_role(RoleName=self.role)
            logger.debug("Policy ARN:" + str(response['Role']['Arn']) + " already exists.")
            return response['Role']['Arn']
        except Exception:
            logger.exception("Failed to create role with exception:")
            return None

    def attach_role_policy_csp(self, policy):
        try:
            logger.debug(
                "Create or check if policy " + str(policy) + " is attached to role " + str(self.role) + " exists.")
            try:
                iam = self.session.client('iam')
                # Create a policy
                response = iam.attach_role_policy(PolicyArn=policy, RoleName=self.role)
                logger.debug("Policy: " + str(response))
                logger.info("Attached policy " + str(policy) + " to role " + str(self.role) + " done.")
            except Exception as e:
                logger.debug(str(e))
                logger.info("Role on AWS named: " + str(self.role) + " and policy named:" + str(
                    policy) + " already attached, nothing to do.")
            return True
        except Exception:
            logger.exception("Failed to attach policy to role with exception:")
            return False

    def instance_profile_csp(self):
        try:
            instance_profile_name = 'AccelizeLoadFPGA'
            logger.debug("Create or check if instance profile  " + str(instance_profile_name) + " exists.")
            try:
                iam = self.session.client('iam')
                instance_profile = iam.create_instance_profile(InstanceProfileName=instance_profile_name)
                time.sleep(5)
                instance_profile.add_role(RoleName=self.role)
                logger.debug("Instance profile: %s", str(instance_profile))
                logger.info("Instance profile %s created", str(instance_profile_name))
            except Exception as e:
                logger.debug(str(e))
                logger.info(
                    "Instance profile on AWS named: :" + str(instance_profile_name) + " already exists, nothing to do.")
            return True
        except Exception:
            logger.exception("Failed to attach policy to role with exception:")
            return False

    def security_group_csp(self):
        try:
            logger.debug("Create or Check if security group '%s' exists.", self.security_group)
            ec2 = self.session.client('ec2')
            public_ip = _CSPGenericClass.get_host_public_ip()  # Find the host public IP
            try:
                response = ec2.describe_vpcs()
                vpc_id = response.get('Vpcs', [{}])[0].get('VpcId', '')
                logger.info("Default VPC: " + str(vpc_id))
                response_create_security_group = ec2.create_security_group(GroupName=self.security_group,
                                                                           Description="Generated by accelize API",
                                                                           VpcId=vpc_id)
                security_group_id = response_create_security_group['GroupId']
                logger.info("Created security group with ID %s in vpc %s", security_group_id, vpc_id)
            except Exception as e:
                logger.debug(str(e))
                logger.info("A security group '%s' is already existing on %s.", self.security_group, self.provider)
            try:
                my_sg = ec2.describe_security_groups(GroupNames=[self.security_group, ], )
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
                logger.debug("Successfully Set " + str(data))
                logger.info("Added in security group '%s': SSH and HTTP for IP %s.", self.security_group, public_ip)
            except Exception as e:
                logger.debug(str(e))
                logger.info("Right for IP " + str(public_ip) + " on AWS already exists, nothing to do.")
            return True
        except Exception:
            logger.exception("Failed to create security group with message:")
            return False

    def get_instance_csp(self):
        if self.instance_id is None:
            logger.warn("No instance ID provided")
            return False
        ec2 = self.session.resource('ec2')
        self.instance = ec2.Instance(self.instance_id)
        try:
            logger.debug("Found an instance with ID %s in the following state: %s", self.instance_id,
                         str(self.instance.state))
            return True
        except Exception:
            logger.error("Could not find an instance with ID %s", self.instance_id)
            return False

    def set_accelerator_requirements(self, accel_parameters):
        if self.region not in accel_parameters.keys():
            logger.error("Region '%s' is not supported. Available regions are: %s", self.region,
                         ', '.join(accel_parameters.keys()))
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
                # Absolutely mandatory to refresh the state of object (state is not updated automatically)
                if not self.get_instance_csp():
                    return None

                status = self.instance.state["Name"]
                logger.debug("Instance status: %s", status)
                if status == "running":
                    break
                time.sleep(5)
            # Waiting for the instance to boot
            logger.info("Instance is now booting...")
            instance_url = self.get_instance_url()
            if not check_url(instance_url, 1, 72, 5, logger=logger):  # 6 minutes timeout
                logger.error("Timed out while waiting CSP instance to boot.")
                return None
            logger.info("Instance booted!")
            return self.instance
        except Exception:
            logger.exception("Caught following exception:")
            return None

    def start_new_instance_csp(self):
        try:
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
        except Exception:
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
                logger.error("Instance ID %s cannot be started because it is not in a valid state (%s).",
                             self.instance_id, state)
                return False
            if not self.wait_instance_ready():
                return False
            return True
        except Exception:
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
        except Exception:
            logger.exception("Caught following exception:")
            return False