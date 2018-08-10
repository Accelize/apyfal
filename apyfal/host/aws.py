# coding=utf-8
"""Amazon Web Services EC2"""

from concurrent.futures import ThreadPoolExecutor as _ThreadPoolExecutor
from contextlib import contextmanager as _contextmanager
from copy import deepcopy as _deepcopy
from json import dumps as _json_dumps
import time as _time

import boto3 as _boto3
from botocore.exceptions import ClientError as _ClientError

from apyfal.host._csp import CSPHost as _CSPHost
import apyfal.exceptions as _exc
import apyfal._utilities as _utl
from apyfal._utilities import get_logger as _get_logger


@_contextmanager
def _exception_handler(
        to_catch=_ClientError, to_raise=None,
        filter_error_codes=None, exception_msg=None, **exc_kwargs):
    """
    Context manager that catch AWS EC2 exceptions and raises
    Apyfal exceptions.

    Args:
        to_catch (Exception or tuple of Exception): Exception to catch.
            ClientError if not specified.
        to_raise (apyfal.exception.AcceleratorException subclass):
            Exception to raise. apyfal.exceptions.HostRuntimeException if not
            specified.
        filter_error_codes (str or tuple of str):
            Don't raise exception if error code in this argument.
        exception_msg (str): Exception message.
        exc_kwargs: Exception to raise arguments.
    """
    # Performs operation
    try:
        yield

    # Catch specified exceptions
    except to_catch as exception:
        # Try to get error code and message
        try:
            error_dict = exception.response['Error']
            error_code = error_dict['Code']
        except (AttributeError, KeyError):
            raise _exc.HostRuntimeException(exception_msg, exc=exception)

        # Converts single str to tuple
        if filter_error_codes is None:
            filter_error_codes = ()
        elif isinstance(filter_error_codes, str):
            filter_error_codes = (filter_error_codes,)

        # Raises if not in filter
        if error_code not in filter_error_codes:
            exception = to_raise or _exc.HostRuntimeException
            raise exception(
                exception_msg, exc=error_dict['Message'], **exc_kwargs)


class AWSHost(_CSPHost):
    """AWS EC2 CSP

    Args:
        host_type (str): Cloud service provider name. Default to "AWS".
        config (apyfal.configuration.Configuration, path-like object or
            file-like object):
            If not set, will search it in current working directory,
            in current user "home" folder. If none found, will use default
            configuration values.
            Path-like object can be path, URL or cloud object URL.
        client_id (str): AWS Access Key ID.
        secret_id (str): AWS Secret Access Key.
        region (str): AWS region. Needs a EC2 region supporting instances with
            FPGA devices.
        instance_type (str): AWS EC2 Instance type.
            Default defined by accelerator.
        key_pair (str): AWS Key pair. Default to 'AccelizeAWSKeyPair'.
        security_group: AWS Security group. Default to 'AccelizeSecurityGroup'.
        instance_id (str): Instance ID of an already existing AWS EC2 instance
            to use. If not specified, create a new instance.
        instance_name_prefix (str): Prefix to add to instance name.
        host_ip (str): IP or URL address of an already existing AWS EC2 instance
            to use. If not specified, create a new instance.
        role (str): AWS IAM role. Generated to allow instance to load AGFI
            (FPGA bitstream). Default to 'AccelizeRole'.
        stop_mode (str or int): Define the "stop" method behavior.
            Default to 'term' if new instance, or 'keep' if already existing
            instance. See "stop_mode" property for more information and possible
            values.
        init_config (bool or apyfal.configuration.Configuration,
            path-like object or file-like object):
            Configuration file to pass to instance on
            initialization. This configuration file will be used as default for
            host side accelerator.
            If value is True, use 'config' configuration.
            If value is a configuration use this configuration.
            If value is None or False, don't passe any configuration file
            (This is default behavior).
        init_script (path-like object or file-like object): A bash script
            to execute on instance startup.
    """
    #: Provider name to use
    NAME = 'AWS'

    #: AWS Website
    DOC_URL = "https://aws.amazon.com"

    STATUS_RUNNING = 'running'
    STATUS_STOPPED = 'stopped'
    STATUS_STOPPING = 'stopping'

    _INFO_NAMES = _CSPHost._INFO_NAMES.copy()
    _INFO_NAMES.update(['_role', '_policy'])

    def __init__(self, role=None, **kwargs):
        _CSPHost.__init__(self, **kwargs)

        # Get AWS specific arguments
        self._role = (role or self._config[self._config_section]['role'] or
                      self._default_parameter_value('Role'))
        self._policy = None

        # Load session
        self._session = _boto3.session.Session(
            aws_access_key_id=self._client_id,
            aws_secret_access_key=self._secret_id, region_name=self._region)

    def _check_credential(self):
        """
        Check CSP credentials.

        Raises:
            apyfal.exceptions.HostAuthenticationException:
                Authentication failed.
        """
        ec2_client = self._session.client('ec2')
        with _exception_handler(to_raise=_exc.HostAuthenticationException):
            ec2_client.describe_key_pairs()

    def _init_key_pair(self):
        """
        Initializes key pair.
        """
        ec2_client = self._session.client('ec2')

        # Checks if Key pairs exists, needs to get the full pairs list
        # and compare in lower case because Boto perform its checks case
        # sensitive and AWS use case insensitive names.
        with _exception_handler():
            key_pairs = ec2_client.describe_key_pairs()

        name_lower = self._key_pair.lower()
        for key_pair in key_pairs['KeyPairs']:
            key_pair_name = key_pair['KeyName']
            if key_pair_name.lower() == name_lower:
                self._key_pair = key_pair_name
                return

        # Key does not exist on the CSP, create it
        ec2_resource = self._session.resource('ec2')
        with _exception_handler():
            key_pair = ec2_resource.create_key_pair(KeyName=self._key_pair)

        _utl.create_key_pair_file(self._key_pair, key_pair.key_material)
        _get_logger().info(_utl.gen_msg(
            "created_named", "key pair", self._key_pair))

    def _init_policy(self):
        """
        Initialize policy.

        This policy allow instance to:
            - Load FPGA bitstream.
            - Access to S3 buckets objects  for read and write.
        """
        # Create a policy
        policy = 'AccelizePolicy'
        policy_document = _json_dumps({
            "Version": "2012-10-17", "Statement": [

                # Grant FPGA access
                {"Sid": "AllowFpgaCommands", "Effect": "Allow",
                 "Action": [
                     "ec2:AssociateFpgaImage", "ec2:DisassociateFpgaImage",
                     "ec2:DescribeFpgaImages"], "Resource": ["*"]},

                # Grant S3 buckets access
                {"Sid": "AllowS3Access", "Effect": "Allow",
                 "Action": ["s3:GetObject", "s3:PutObject"],
                 "Resource": ["arn:aws:s3:::*"]}]})

        iam_client = self._session.client('iam')
        with _exception_handler(filter_error_codes='EntityAlreadyExists'):
            iam_client.create_policy(
                PolicyName=policy, PolicyDocument=policy_document)

            _get_logger().info(_utl.gen_msg('created_named', 'policy', policy))

        iam_client = self._session.client('iam')
        with _exception_handler():
            response = iam_client.list_policies(
                Scope='Local', OnlyAttached=False, MaxItems=100)
        for policy_item in response['Policies']:
            if policy_item['PolicyName'] == policy:
                self._policy = policy_item['Arn']
                return

        raise _exc.HostConfigurationException(
            gen_msg=('created_failed_named', 'policy', policy))

    def _init_role(self):
        """
        Initialize IAM role.

        This role allow to perform actions defined by policy.
        """
        assume_role_policy_document = _json_dumps({
            "Version": "2012-10-17", "Statement": {
                "Effect": "Allow",
                "Principal": {"Service": "ec2.amazonaws.com"},
                "Action": "sts:AssumeRole"}})

        iam_resource = self._session.resource('iam')
        with _exception_handler(filter_error_codes='EntityAlreadyExists'):
            role = iam_resource.create_role(
                RoleName=self._role,
                AssumeRolePolicyDocument=assume_role_policy_document,
                Description=_utl.gen_msg('accelize_generated'))

            _get_logger().info(_utl.gen_msg('created_named', 'IAM role', role))

        iam_client = self._session.client('iam')
        with _exception_handler():
            arn = iam_client.get_role(RoleName=self._role)['Role']['Arn']

        return arn

    def _attach_role_policy(self):
        """
        Attach policy to IAM role.
        """
        iam_client = self._session.client('iam')

        with _exception_handler(filter_error_codes='EntityAlreadyExists'):
            iam_client.attach_role_policy(
                PolicyArn=self._policy, RoleName=self._role)

            _get_logger().info(_utl.gen_msg(
                'attached_to', 'policy', self._policy, 'IAM role', self._role))

    def _init_instance_profile(self):
        """
        Initialize instance profile.

        This instance_profile allow to perform actions defined by role.
        """
        iam_client = self._session.client('iam')

        # Create instance profile
        instance_profile_name = 'AccelizeLoadFPGA'
        with _exception_handler(filter_error_codes='EntityAlreadyExists'):
            iam_client.create_instance_profile(
                InstanceProfileName=instance_profile_name)

            _get_logger().info(_utl.gen_msg(
                'created_object', 'instance profile', instance_profile_name))

            _time.sleep(5)

        # Attach role to instance profile
        with _exception_handler(filter_error_codes='LimitExceeded'):
            iam_client.add_role_to_instance_profile(
                InstanceProfileName=instance_profile_name, RoleName=self._role)

            _get_logger().info(_utl.gen_msg(
                'attached_to', 'role', self._role, 'instance profile',
                instance_profile_name))

    def _init_security_group(self):
        """
        Initialize CSP security group.
        """
        # Get list of security groups
        # Checks if Key pairs exists, like for key pairs
        # needs  case insensitive names check
        ec2_client = self._session.client('ec2')
        with _exception_handler():
            security_groups = ec2_client.describe_security_groups()

        name_lower = self._security_group.lower()
        group_exists = False
        security_group_id = ''
        for security_group in security_groups['SecurityGroups']:
            group_name = security_group['GroupName']
            if group_name.lower() == name_lower:
                # Update name
                self._security_group = group_name

                # Get group ID
                security_group_id = security_group['GroupId']

                # Mark as existing
                group_exists = True
                break

        # Try to create security group if not exist
        if not group_exists:
            # Get VPC
            with _exception_handler():
                vpc_id = ec2_client.describe_vpcs().get(
                    'Vpcs', [{}])[0].get('VpcId', '')

            with _exception_handler():
                response = ec2_client.create_security_group(
                    GroupName=self._security_group,
                    Description=_utl.gen_msg('accelize_generated'),
                    VpcId=vpc_id)

            # Get group ID
            security_group_id = response['GroupId']

            _get_logger().info(_utl.gen_msg(
                'created_named', 'security group', security_group_id))

        # Add host IP to security group if not already done
        public_ip = _utl.get_host_public_ip()

        ip_permissions = []
        for port in self.ALLOW_PORTS:
            ip_permissions.append({
                'IpProtocol': 'tcp', 'FromPort': port, 'ToPort': port,
                'IpRanges': [{'CidrIp': public_ip}]})

        with _exception_handler(
                filter_error_codes='InvalidPermission.Duplicate'):
            ec2_client.authorize_security_group_ingress(
                GroupId=security_group_id, IpPermissions=ip_permissions)

        _get_logger().info(
            _utl.gen_msg('authorized_ip', public_ip, self._security_group))

    def _get_instance(self):
        """
        Returns current instance.

        Returns:
            object: Instance
        """
        with _exception_handler(gen_msg=('no_instance_id', self._instance_id)):
            return self._session.resource('ec2').Instance(self._instance_id)

    def _get_public_ip(self):
        """
        Read current instance public IP from CSP instance.

        Returns:
            str: IP address
        """
        with _exception_handler(gen_msg='no_instance_ip'):
            return self._instance.public_ip_address

    def _get_private_ip(self):
        """
        Read current instance private IP from CSP instance.

        Returns:
            str: IP address
        """
        with _exception_handler(gen_msg='no_instance_ip'):
            return self._instance.private_ip_address

    def _get_status(self):
        """
        Returns current status of current instance.

        Returns:
            str: Status
        """
        with _utl.Timeout(1, sleep=0.01) as timeout:
            while True:
                # Check Timeout
                if timeout.reached():
                    raise _exc.HostRuntimeException(gen_msg=(
                        'no_instance_id', self._instance_id))

                # Get status
                with _exception_handler(
                        filter_error_codes='InvalidInstanceID.NotFound'):
                    return self._instance.state["Name"]

    def get_configuration_env(self, **kwargs):
        """
        Return environment to pass to
        "apyfal.accelerator.AcceleratorClient.start"
        "csp_env" argument.

        Args:
            kwargs:

        Returns:
            dict: Configuration environment.
        """
        current_env = _deepcopy(self._config_env)

        try:
            current_env['AGFI'] = kwargs['AGFI']
        except KeyError:
            pass
        else:
            import warnings
            warnings.warn(
                "Overwrite AGFI factory requirements with custom configuration")
        return current_env

    def _create_instance(self):
        """
        Initialize and create instance.
        """
        futures = []
        with _ThreadPoolExecutor(max_workers=6) as executor:
            # Run configuration in parallel
            policy = executor.submit(self._init_policy)
            role = executor.submit(self._init_role)
            for method in (self._init_key_pair, self._init_instance_profile,
                           self._init_security_group):
                futures.append(executor.submit(method))

            # Wait that role and policy are completed to attach them
            role.result()
            policy.result()
            futures.append(executor.submit(self._attach_role_policy))

        # Wait completion
        for future in futures:
            future.result()

        # Sets AGFI
        self._config_env = {'AGFI': self._region_parameters['fpgaimage']}

    def _start_new_instance(self):
        """
        Start a new instance.

        Returns:
            object: Instance
            str: Instance ID
        """
        # Base arguments
        kwargs = dict(
            ImageId=self._image_id, InstanceType=self._instance_type,
            KeyName=self._key_pair, SecurityGroups=[self._security_group],
            IamInstanceProfile={'Name': 'AccelizeLoadFPGA'},
            InstanceInitiatedShutdownBehavior='stop',
            TagSpecifications=[{'ResourceType': 'instance', 'Tags': [
                {'Key': 'Generated',
                 'Value': _utl.gen_msg('accelize_generated')},
                {'Key': 'Name', 'Value': self._get_instance_name()}]}],
            MinCount=1, MaxCount=1,)

        # Optional arguments
        user_data = self._user_data
        if user_data:
            kwargs['UserData'] = user_data

        # Create instance
        with _exception_handler():
            instance = self._session.resource('ec2').create_instances(
                **kwargs)[0]

        return instance, instance.id

    def _start_existing_instance(self, status):
        """
        Start a existing instance.

        Args:
            status (str): Status of the instance.
        """
        # Waiting for the instance stop if currently stopping
        if status == self.STATUS_STOPPING:
            with _utl.Timeout(self.TIMEOUT) as timeout:
                while True:
                    # Get instance status
                    status = self._status()
                    if status != self.STATUS_STOPPING:
                        break
                    elif timeout.reached():
                        raise _exc.HostRuntimeException(gen_msg=(
                            'timeout_status', 'stop', status))

        # If instance stopped, starts it
        if status == self.STATUS_STOPPED:
            with _exception_handler():
                self._instance.start()

        # If another status, raises error
        elif status != self.STATUS_RUNNING:
            raise _exc.HostRuntimeException(gen_msg=(
                'unable_to_status', 'start', status))

    def _terminate_instance(self):
        """
        Terminate and delete instance.
        """
        if self._instance is not None:
            with _exception_handler():
                return self._instance.terminate()

    def _pause_instance(self):
        """
        Pause instance.
        """
        if self._instance is not None:
            with _exception_handler():
                return self._instance.stop()

    def _iter_hosts(self):
        """
        Iterates over accelerator hosts of current type.

        Returns:
            generator of dict: dicts contains attributes values of the host.
        """
        ec2_resource = self._session.resource('ec2')

        with _exception_handler():
            for instance in ec2_resource.instances.filter(
                    Filters=[{'Name': 'instance-state-name',
                              'Values': ['running']}]):
                instance_name = [instance.tags[index]['Value']
                                 for index in range(len(instance.tags))
                                 if instance.tags[index]['Key'] == 'Name'][0]

                # Yields only matching accelerator instances
                if self._is_accelerator_host(instance_name):
                    yield dict(
                        instance_id=instance.id,
                        instance_type=instance.instance_type,
                        private_ip=instance.private_ip_address,
                        public_ip=instance.public_ip_address,
                        instance_name=instance_name,
                        security_group=instance.security_groups[0]['GroupName'],
                        image_id=instance.image_id,
                        key_pair=instance.key_name)
