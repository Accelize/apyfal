# coding=utf-8
"""Amazon Web Services"""

from copy import deepcopy as _deepcopy
from json import dumps as _json_dumps
import time as _time

import boto3 as _boto3
import botocore.exceptions as _boto_exceptions

from acceleratorAPI.csp import CSPGenericClass as _CSPGenericClass
import acceleratorAPI.exceptions as _exc
import acceleratorAPI._utilities as _utl
from acceleratorAPI._utilities import get_logger as _get_logger


class AWSClass(_CSPGenericClass):
    """AWS CSP Class

    Args:
        provider (str): Cloud service provider name. Default to "AWS".
            If set will override value from configuration file.
        config (str or acceleratorAPI.configuration.Configuration): Configuration file path or instance.
            If not set, will search it in current working directory, in current
            user "home" folder. If none found, will use default configuration values.
        client_id (str):CSP Client ID. See with your provider to generate this value.
            If set will override value from configuration file.
        secret_id (str):CSP secret ID. See with your provider to generate this value.
            If set will override value from configuration file.
        region (str): CSP region. Check with your provider which region are using instances with FPGA.
             If set will override value from configuration file.
        instance_type:
        ssh_key (str): SSH key to use with your CSP. If set will override value from configuration file.
        security_group:
        instance_id (str): CSP Instance ID to reuse. If set will override value from configuration file.
        instance_url (str): CSP Instance URL or IP address to reuse. If set will override value from configuration file.
        role:
        stop_mode (int): Define the "stop_instance" method behavior. See "stop_mode"
            property for more information and possible values.
        exit_instance_on_signal (bool): If True, exit CSP instances
            on OS exit signals. This may help to not have instance still running
            if Python interpreter is not exited properly. Note: this is provided for
            convenience and does not cover all exit case like process kill and
            may not work on all OS.
    """
    CSP_NAME = 'AWS'
    CSP_HELP_URL = "https://aws.amazon.com"

    def __init__(self, **kwargs):
        _CSPGenericClass.__init__(self, **kwargs)

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
            ec2_client.describe_key_pairs()
        except ec2_client.exceptions.ClientError as exception:
            raise _exc.CSPAuthenticationException(exc=exception)

    def _init_ssh_key(self):
        """
        Initialize SSH key.

        Returns:
            bool: True if reuse existing key
        """
        ec2_client = self._session.client('ec2')

        # Checks if Key pairs exists
        try:
            ec2_client.describe_key_pairs(KeyNames=[self._ssh_key])
            return True

        # Key does not exist on the CSP, create it
        except ec2_client.exceptions.ClientError:
            # TODO: to catch properly

            ec2_resource = self._session.resource('ec2')
            key_pair = ec2_resource.create_key_pair(KeyName=self._ssh_key)

            _utl.create_ssh_key_file(self._ssh_key, key_pair.key_material)

            return False

    def _init_policy(self, policy):
        """
        Initialize CSP policy.

        Args:
            policy:
        """
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
            iam_client.create_policy(
                PolicyName=policy, PolicyDocument=policy_document)

        except iam_client.exceptions.EntityAlreadyExistsException:
            # TODO: check if cached properly
            pass
        else:
            _get_logger().info(
                "Created policy on AWS named %s to allow FPGA loading ", policy)

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

        except _boto_exceptions.ClientError:
            # TODO: to catch properly
            pass
        else:
            _get_logger().info(
                "Created role on AWS named %s to allow FPGA loading ", role)

        iam_client = self._session.client('iam')
        arn = iam_client.get_role(RoleName=self._role)['Role']['Arn']

        return arn

    def _attach_role_policy(self, policy_arn):
        """
        Attach policy to role.

        Args:
            policy_arn (str): Policy ARN
        """
        iam_client = self._session.client('iam')
        try:
            # Create a policy
            iam_client.attach_role_policy(
                PolicyArn=policy_arn, RoleName=self._role)

        except iam_client.exceptions.EntityAlreadyExistsException:
            # TODO: check if cached properly
            pass

        else:
            _get_logger().info("Attached policy '%s' to role '%s'.", policy_arn, self._role)

    def _init_instance_profile(self):
        """
        Initialize instance profile.
        """
        instance_profile_name = 'AccelizeLoadFPGA'

        iam_client = self._session.client('iam')
        try:
            instance_profile = iam_client.create_instance_profile(
                InstanceProfileName=instance_profile_name)

        except iam_client.exceptions.EntityAlreadyExistsException:
            # TODO: check if cached properly

            # TODO: Get already existing instance_profile and then attach role in both cases
            pass

        else:
            _time.sleep(5)

            # Attach role to instance profile
            instance_profile.add_role(RoleName=self._role)
            _get_logger().info(
                "Attachd role '%s' to instance profile '%s' to allow FPGA loading ",
                self._role, instance_profile_name)

    def _init_security_group(self):
        """
        Initialize CSP security group.
        """
        ec2_client = self._session.client('ec2')

        # Get VPC
        vpc_id = ec2_client.describe_vpcs().get('Vpcs', [{}])[0].get('VpcId', '')

        # Try to create security group if not exist
        try:
            response_create_security_group = ec2_client.create_security_group(
                GroupName=self._security_group,
                Description="Generated by accelize API", VpcId=vpc_id)
            security_group_id = response_create_security_group['GroupId']
        except ec2_client.exceptions.ClientError:
            # TODO: to catch properly
            # TODO: except if error with VPC
            pass
        else:
            _get_logger().info("Created security group with ID %s in vpc %s", security_group_id, vpc_id)

        # Add host IP to security group if not already done
        public_ip = _utl.get_host_public_ip()
        my_sg = ec2_client.describe_security_groups(GroupNames=[self._security_group, ], )
        try:
            rules = ec2_client.authorize_security_group_ingress(
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
        except ec2_client.exceptions.ClientError:
            # TODO: to catch properly
            pass
        else:
            _get_logger().info("Added in security group '%s': SSH and HTTP for IP %s.",
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
            raise _exc.CSPInstanceException("Could not return instance URL", exc=exception)

    def _get_instance_private_ip(self):
        """
        Read current instance private IP from CSP instance.

        Returns:
            str: IP address
        """
        try:
            return self._instance.private_ip_address
        except _boto_exceptions.ClientError as exception:
            raise _exc.CSPInstanceException("Could not return instance URL", exc=exception)

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
                "Could not find an instance with ID %s", self._instance_id, exc=exception)
        return instance_state["Name"]

    def _get_config_env_from_region(self, accel_parameters_in_region):
        """
        Read accelerator parameters and get configuration environment.

        Args:
            accel_parameters_in_region (dict): AcceleratorClient parameters
                for the current CSP region.

        Returns:
            dict: configuration environment
        """
        return {'AGFI': accel_parameters_in_region['fpgaimage']}

    def get_configuration_env(self, **kwargs):
        """
        Return environment to pass to
        "acceleratorAPI.accelerator.AcceleratorClient.start"
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
            pass
        else:
            import warnings
            warnings.warn(
                "Overwrite AGFI factory requirements with custom configuration:\n%s",
                _utl.pretty_dict(kwargs['AGFI']))
        return currenv

    def _create_instance(self):
        """
        Initialize and create instance.
        """
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
        time_0 = _time.time()
        while _time.time() - time_0 < 360.0:
            # Get instance status
            status = self.instance_status()
            if status == "running":
                return
            _time.sleep(1)

        raise _exc.CSPInstanceException(
            "Timed out while waiting CSP instance provisioning (last status: %s)." %
            status)

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
            self._instance.start()

        elif state != "running":
            raise _exc.CSPInstanceException(
                "Instance ID %s cannot be started because it is not in a valid state (%s).",
                self._instance_id, state)

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
