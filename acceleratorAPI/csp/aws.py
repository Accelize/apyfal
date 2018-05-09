# coding=utf-8
"""Amazon Web Services"""

from copy import deepcopy as _deepcopy
from json import dumps as _json_dumps
from time import sleep as _sleep

import boto3 as _boto3
import botocore.exceptions as _boto_exceptions

import acceleratorAPI._utilities as _utl
import acceleratorAPI.csp as _csp
import acceleratorAPI.exceptions as _exc
from acceleratorAPI import logger


class AWSClass(_csp.CSPGenericClass):
    """AWS CSP Class"""
    CSP_HELP_URL = "https://aws.amazon.com"

    def __init__(self, **kwargs):
        _csp.CSPGenericClass.__init__(self, **kwargs)

        # Checks mandatory configuration values
        self._check_arguments('role')

        # Load session
        self._session = _boto3.session.Session(
            aws_access_key_id=self._client_id,
            aws_secret_access_key=self._secret_id,
            region_name=self._region
        )

    def check_credential(self):
        """
        Check CSP credentials.

        Raises:
            acceleratorAPI.exceptions.CSPAuthenticationException:
                Authentication failed.
        """
        ec2_client = self._session.client('ec2')
        try:
            response = ec2_client.describe_key_pairs()
        except ec2_client.exceptions.ClientError as exception:
            logger.debug(str(exception))
            raise _exc.CSPAuthenticationException()
        logger.debug("Response of 'describe_key_pairs': %s", response)

    def _init_ssh_key(self):
        """
        Initialize CSP SSH key.
        """
        logger.debug("Create or check if KeyPair %s exists.", self._ssh_key)
        ec2_client = self._session.client('ec2')

        # Checks if Key pairs exists
        try:
            key_pair = ec2_client.describe_key_pairs(KeyNames=[self._ssh_key])

        # Key does not exist on the CSP, create it
        except ec2_client.exceptions.ClientError as exception:

            logger.debug(str(exception))
            logger.info("Create KeyPair %s", str(self._ssh_key))

            ec2_resource = self._session.resource('ec2')
            key_pair = ec2_resource.create_key_pair(KeyName=self._ssh_key)

            _utl.create_ssh_key_file(self._ssh_key, key_pair.key_material)

        # Key does exist on the CSP
        else:
            logger.info("KeyPair '%s' is already existing on %s.", key_pair['KeyPairs'][0]['KeyName'],
                        self._provider)

    def _init_policy(self, policy):
        """
        Initialize CSP policy.

        Args:
            policy:
        """
        logger.debug("Create or check if policy '%s' exists.", policy)

        # Create a policy
        policy_document = _json_dumps({
            "Version": "2012-10-17",
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
        })

        iam_client = self._session.client('iam')
        try:
            response = iam_client.create_policy(
                PolicyName=policy, PolicyDocument=policy_document)

        except iam_client.exceptions.EntityAlreadyExistsException as exception:
            logger.debug(str(exception))
            logger.info("Policy on AWS named: %s already exists, nothing to do.", policy)
        else:
            logger.debug("Policy: %s", response)

        iam_client = self._session.client('iam')
        response = iam_client.list_policies(
            Scope='Local', OnlyAttached=False, MaxItems=100)
        for policy_item in response['Policies']:
            if policy_item['PolicyName'] == policy:
                return policy_item['Arn']

        raise _exc.CSPConfigurationException(
            "Failed to create policy. Unable to find policy 'Arn'.")

    def _init_role(self):
        """
        Initialize CSP role.
        """
        logger.debug("Create or check if role %s exists", self._role)

        assume_role_policy_document = _json_dumps({
            "Version": "2012-10-17",
            "Statement": {
                "Effect": "Allow",
                "Principal": {"Service": "ec2.amazonaws.com"},
                "Action": "sts:AssumeRole"
            }
        })

        iam_resource = self._session.resource('iam')
        try:
            role = iam_resource.create_role(
                RoleName=self._role,
                AssumeRolePolicyDocument=assume_role_policy_document,
                Description='Created automatically'
            )
            logger.debug("role: %s", str(role))

        except _boto_exceptions.ClientError as exception:
            logger.debug(str(exception))
            logger.info("Role on AWS named: %s already exists, nothing to do.",
                        self._role)

        iam_client = self._session.client('iam')
        arn = iam_client.get_role(RoleName=self._role)['Role']['Arn']

        logger.debug("Policy ARN:'%s' already exists.", arn)
        return arn

    def _attach_role_policy(self, policy_arn):
        """
        Attach policy to role.

        Args:
            policy_arn (str): Policy ARN
        """
        logger.debug(
            "Create or check if policy '%s' is attached to role '%s' exists.",
            policy_arn, self._role)

        iam_client = self._session.client('iam')
        try:
            # Create a policy
            response = iam_client.attach_role_policy(
                PolicyArn=policy_arn, RoleName=self._role)

        except iam_client.exceptions.EntityAlreadyExistsException as exception:
            logger.debug(str(exception))
            logger.info(
                "Role on AWS named: '%s' and policy named: '%s' already attached, nothing to do.",
                self._role, policy_arn)

        else:
            logger.debug("Policy: %s", response)
            logger.info("Attached policy '%s' to role '%s' done.", policy_arn, self._role)

    def _init_instance_profile(self):
        """
        Initialize instance profile.
        """
        instance_profile_name = 'AccelizeLoadFPGA'
        logger.debug("Create or check if instance profile '%s' exists.",
                     instance_profile_name)

        iam_client = self._session.client('iam')
        try:
            instance_profile = iam_client.create_instance_profile(
                InstanceProfileName=instance_profile_name)

        except iam_client.exceptions.EntityAlreadyExistsException as exception:
            logger.debug(str(exception))
            logger.info(
                "Instance profile on AWS named: '%s' already exists, nothing to do.",
                instance_profile_name)

        else:
            _sleep(5)
            instance_profile.add_role(RoleName=self._role)
            logger.debug("Instance profile: %s", instance_profile)
            logger.info("Instance profile %s created", instance_profile_name)

    def _init_security_group(self):
        """
        Initialize CSP security group.
        """
        logger.debug("Create or Check if security group '%s' exists.",
                     self._security_group)

        ec2_client = self._session.client('ec2')

        # Get VPC
        vpc_id = ec2_client.describe_vpcs().get('Vpcs', [{}])[0].get('VpcId', '')
        logger.info("Default VPC: %s", vpc_id)

        # Try to create security group if not exist
        try:
            response_create_security_group = ec2_client.create_security_group(
                GroupName=self._security_group,
                Description="Generated by accelize API", VpcId=vpc_id)
            security_group_id = response_create_security_group['GroupId']
        except ec2_client.exceptions.ClientError as exception:
            logger.debug(str(exception))
            logger.info("A security group '%s' is already existing on %s.",
                        self._security_group, self._provider)
        else:
            logger.info("Created security group with ID %s in vpc %s", security_group_id, vpc_id)

        # Add host IP to security group if not already done
        public_ip = _utl.get_host_public_ip(logger)
        my_sg = ec2_client.describe_security_groups(GroupNames=[self._security_group, ], )
        try:
            data = ec2_client.authorize_security_group_ingress(
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
        except ec2_client.exceptions.ClientError as exception:
            logger.debug(str(exception))
            logger.info("Right for IP '%s' on AWS already exists, nothing to do.", public_ip)
        else:
            logger.debug("Successfully Set '%s'", data)
            logger.info("Added in security group '%s': SSH and HTTP for IP %s.",
                        self._security_group, public_ip)

    def _get_instance(self):
        """
        Returns current instance.

        Returns:
            object: Instance
        """
        return self._session.resource('ec2').Instance(self._instance_id)

    def _get_instance_public_ip(self):
        """
        Read current instance public IP from CSP instance.

        Returns:
            str: IP address
        """
        try:
            return self._instance.public_ip_address
        except _boto_exceptions.ClientError as exception:
            raise _exc.CSPInstanceException("Could not return instance URL ('%s')" % exception)

    def _get_instance_status(self):
        """
        Returns current status of current instance.

        Returns:
            str: Status
        """
        try:
            instance_state = self._instance.state
        except _boto_exceptions.ClientError as exception:
            raise _exc.CSPInstanceException(
                "Could not find an instance with ID %s ('%s')", self._instance_id, exception)
        else:
            logger.debug("Found an instance with ID %s in the following state: %s",
                         self._instance_id, instance_state)
        return instance_state["Name"]

    def _read_accelerator_parameters(self, accel_parameters_in_region):
        """
        Read accelerator parameters and get information required
        to configure CSP instance accordingly.

        Args:
            accel_parameters_in_region (dict): Accelerator parameters
                for the current CSP region.

        Returns:
            str: image_id
            str: instance_type
            dict: config_env
        """
        config_env = {'AGFI': accel_parameters_in_region['fpgaimage']}
        image_id = accel_parameters_in_region['image']
        instance_type = accel_parameters_in_region['instancetype']

        logger.debug("Set image ID: %s", image_id)
        logger.debug("Set instance type: %s", instance_type)

        return image_id, instance_type, config_env

    def get_configuration_env(self, **kwargs):
        """
        Return environment to pass to
        "acceleratorAPI.accelerator.Accelerator.start_accelerator"
        "csp_env" argument.

        Args:
            kwargs:

        Returns:
            dict: Configuration environment.
        """
        currenv = _deepcopy(self._config_env)

        try:
            currenv['AGFI'] = kwargs['AGFI']
        except KeyError:
            logger.debug("Using factory configuration: %s", _utl.pretty_dict(currenv))
        else:
            logger.warning("Overwrite factory requirements with custom configuration:\n%s",
                           _utl.pretty_dict(currenv))
        return currenv

    def _create_instance(self):
        """
        Initialize and create instance.
        """
        self._init_ssh_key()
        policy_arn = self._init_policy('AccelizePolicy')
        self._init_role()
        self._init_instance_profile()
        self._attach_role_policy(policy_arn)
        self._init_security_group()

    def _wait_instance_ready(self):
        """
        Wait until instance is ready.
        """
        # Waiting for the instance provisioning
        logger.info("Waiting for the instance provisioning on %s...", self._provider)
        while True:
            # Get instance status
            status = self.instance_status()
            logger.debug("Instance status: %s", status)
            if status == "running":
                break
            _sleep(5)

    def _start_new_instance(self):
        """
        Start a new instance.

        Returns:
            object: Instance
            str: Instance ID
        """
        instance = self._session.resource('ec2').create_instances(
            ImageId=self._image_id,
            InstanceType=self._instance_type,
            KeyName=self._ssh_key,
            SecurityGroups=[self._security_group],
            IamInstanceProfile={'Name': 'AccelizeLoadFPGA'},
            InstanceInitiatedShutdownBehavior='stop',
            TagSpecifications=[{
                'ResourceType': 'instance',
                'Tags': [
                    {'Key': 'Generated',
                     'Value': 'Accelize script'},
                    {'Key': 'Name',
                     'Value': "Accelize accelerator %s" % self._accelerator}
                ]}],
            MinCount=1, MaxCount=1)[0]

        return instance, instance.id

    def _start_existing_instance(self, state):
        """
        Start a existing instance.

        Args:
            state (str): Status of the instance.
        """
        if state == "stopped":
            response = self._instance.start()
            logger.debug("start response: %s", response)

        elif state != "running":
            raise _exc.CSPInstanceException(
                "Instance ID %s cannot be started because it is not in a valid state (%s).",
                self._instance_id, state)

    def _log_instance_info(self):
        """
        Print some instance information in logger.
        """
        logger.info("Region: %s", self._session.region_name)
        logger.info("Private IP: %s", self._instance.private_ip_address)
        logger.info("Public IP: %s", self.instance_ip)

    def _terminate_instance(self):
        """
        Terminate and delete instance.
        """
        return self._instance.terminate()

    def _pause_instance(self):
        """
        Pause instance.
        """
        return self._instance.stop()
