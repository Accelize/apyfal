# coding=utf-8
"""Alibaba Cloud ECS"""
from base64 import b64encode as _b64encode
from concurrent.futures import (ThreadPoolExecutor as _ThreadPoolExecutor,
                                as_completed as _as_completed)
import json as _json
from uuid import uuid1 as _uuid

from aliyunsdkcore.client import AcsClient as _AcsClient
import aliyunsdkcore.acs_exception.exceptions as _acs_exceptions
import aliyunsdkcore.request as _acs_request

from apyfal.host._csp import CSPHost as _CSPHost
import apyfal.exceptions as _exc
import apyfal._utilities as _utl
from apyfal._utilities import get_logger as _get_logger

# Set HTTPS by default for requests, require "pyopenssl" package
_acs_request.set_default_protocol_type("https")

#: Alibaba Cloud API version (Key is subdomain name, value is API version)
API_VERSION = {'ecs': '2014-05-26',
               'ram': '2015-05-01',
               'sts': '2015-04-01'}

#: Alibaba Cloud API main domain
MAIN_DOMAIN = 'aliyuncs.com'


class AlibabaCSP(_CSPHost):
    """Alibaba Cloud CSP Class

    Args:
        host_type (str): Cloud service provider name. (Default to "Alibaba").
        config (apyfal.configuration.Configuration, path-like object or
            file-like object):
            If not set, will search it in current working directory,
            in current user "home" folder. If none found, will use default
            configuration values.
            Path-like object can be path, URL or cloud object URL.
        client_id (str): Alibaba Access Key ID.
        secret_id (str): Alibaba Secret Access Key.
        region (str): Alibaba region. Needs a region supporting instances with
            FPGA devices.
        instance_type (str): Alibaba instance type.
            Default defined by accelerator.
        key_pair (str): Alibaba Key pair. Default to 'AccelizeAlibabaKeyPair'.
        security_group: Alibaba Security group.
            Default to'AccelizeSecurityGroup'.
        instance_id (str): Instance ID of an already existing Alibaba ECS
            instance to use. If not specified, create a new instance.
        host_name_prefix (str): Prefix to add to instance name.
        host_ip (str): IP or URL address of an already existing Alibaba ECS
            instance to use. If not specified, create a new instance.
        role (str): Alibaba RAM role. Generated to allow instance to load
            FPGA bitstream and access to OSS. Default to 'AccelizeRole'.
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
    #: Provider name
    NAME = "Alibaba"

    #: Alibaba Website
    DOC_URL = 'https://www.alibabacloud.com'

    STATUS_RUNNING = 'Running'
    STATUS_STOPPED = 'Stopped'

    _INFO_NAMES = _CSPHost._INFO_NAMES.copy()
    _INFO_NAMES.update(['_role', '_policy'])

    def __init__(self, role=None, **kwargs):
        _CSPHost.__init__(self, **kwargs)

        # Default some attributes
        self._security_group_id = None
        self._role = (role or self._config[self._config_section]['role'] or
                      self._default_parameter_value('Role'))
        self._policy = self._default_parameter_value('Policy')

        # ClientToken guarantee idempotence of requests
        self._client_token = str(_uuid())

    def _request(self, action_name, domain='ecs',
                 error_code_filter=None, error_code_ignore=None,
                 exception_message=None, **parameters):
        """
        Performs a request on Alibaba cloud.

        Args:
            action_name (str): Action name.
            domain (str): Alibaba cloud subdomain name.
            error_code_filter (str or tuple of str): Filter error codes and
                raise original exception if found. Else raise
                apyfal.exceptions.HostException subclass)
            error_code_ignore (str or tuple of str): Error codes to ignore and
                continue.
            exception_message (str): Exception message if exception to raise.
            parameters: request parameters

        Returns:
            dict: Request response.
        """
        # Checks credentials and init session
        self._check_credential()

        # Creates request
        request = _acs_request.CommonRequest(
            domain='%s.%s' % (domain, MAIN_DOMAIN),
            version=API_VERSION[domain],
            action_name=action_name)

        # Ensures HTTPS use in requests
        request.set_protocol_type("https")

        # Ensures idempotence of the request
        parameters.setdefault('ClientToken', self._client_token)

        # Adds parameters to request
        for parameter in parameters:
            # Formats parameter value to proper string representation
            value = parameters[parameter]
            if not isinstance(value, str):
                # Non string values needs their JSON equivalent
                value = _json.dumps(value)

            # Adds parameter
            request.add_query_param(parameter, value)

        # Performs request
        try:
            response = self._session.do_action_with_exception(request)

        # Handles exceptions
        except (_acs_exceptions.ClientException,
                _acs_exceptions.ServerException) as acs_exception:

            error_code = acs_exception.get_error_code()
            error_msg = acs_exception.get_error_msg()

            # Filters error codes to re-raise as it.
            if error_code_ignore:
                # Forces filter as tuple object
                if isinstance(error_code_ignore, str):
                    error_code_ignore = (error_code_ignore,)

                for code in error_code_ignore:
                    if error_code.startswith(code):
                        return

            if error_code_filter:
                # Forces filter as tuple object
                if isinstance(error_code_filter, str):
                    error_code_filter = (error_code_filter,)

                # Re-raises as it if found
                for code in error_code_filter:
                    if error_code.startswith(code):
                        raise

            # Selects exception type
            if 'AccessKey' in error_code:
                exception = _exc.HostAuthenticationException
            elif 'Invalid' in error_code:
                exception = _exc.HostConfigurationException
            else:
                exception = _exc.HostRuntimeException

            # Raises Apyfal exception
            raise exception(
                exception_message,
                exc='%s: %s' % (error_code, error_msg))

        # Returns response
        return _json.loads(response)

    def _instance_request(self, action_name, status_desc='', **parameters):
        """
        Changes instance status. Does it in a retry loop to be sure
        to have the correct status when performing action.

        Getting status information seem to not always return an up to
        date information and is not reliable to perform requests without error.

        see "AlibabaCSP._request" for more information on requests and
        parameters.

        Args:
            action_name (str): Action name.
            status_desc (str): Status name for description
                (starting, stopping, ...)
            parameters: Request extra parameters.

        Returns:
            dict: Request response.
        """
        instance_id = parameters.pop('InstanceId', self._instance_id)
        with _utl.Timeout(self.TIMEOUT) as timeout:
            while True:
                # Tries to execute requests
                try:
                    return self._request(
                        action_name,
                        error_code_filter='IncorrectInstanceStatus',
                        InstanceId=instance_id, **parameters)

                # If incorrect instance status, waits and retries
                except _acs_exceptions.ServerException:
                    if timeout.reached():
                        raise _exc.HostRuntimeException(gen_msg=(
                            'timeout', status_desc))

    def _get_public_ip(self):
        """
        Read current instance public IP from CSP instance.

        Returns:
            str: IP address
        """
        try:
            return self._get_instance()['PublicIpAddress']['IpAddress'][0]
        except (KeyError, IndexError):
            raise _exc.HostRuntimeException(gen_msg='no_instance_ip')

    def _get_private_ip(self):
        """
        Read current instance private IP from CSP instance.

        Returns:
            str: IP address
        """
        try:
            return self._get_instance()['PrivateIpAddress']['IpAddress'][0]
        except (KeyError, IndexError):
            raise _exc.HostRuntimeException(gen_msg='no_instance_ip')

    def _check_credential(self):
        """
        Check CSP credentials.

        Raises:
            apyfal.exceptions.HostAuthenticationException:
                Authentication failed.
        """
        if self._session is None:
            try:
                self._session = _AcsClient(
                    self._client_id, self._secret_id, self._region)
            except _acs_exceptions.ClientException as exception:
                raise _exc.HostAuthenticationException(exc=exception)

    def _get_status(self):
        """
        Returns current status of current instance.

        Returns:
            str: Status
        """
        try:
            return self._get_instance()['Status']
        except KeyError:
            raise _exc.HostRuntimeException(
                gen_msg=('no_instance_id', self._instance_id))

    def _get_instance(self):
        """
        Returns current instance.

        Returns:
            dict: Instance description
        """
        response = self._request(
            'DescribeInstances', InstanceIds=[self._instance_id])
        try:
            return response['Instances']['Instance'][0]
        except (KeyError, IndexError):
            raise _exc.HostRuntimeException(
                gen_msg=('no_instance_id', self._instance_id))

    def _init_key_pair(self):
        """
        Initializes key pair.

        Returns:
            bool: True if reuses existing key
        """
        response = self._request(
            'DescribeKeyPairs', KeyPairName=self._key_pair)

        # Checks if key pair exists
        lower_name = self._key_pair.lower()
        for key_pair in response['KeyPairs']['KeyPair']:
            key_pair_name = key_pair['KeyPairName']
            if key_pair_name.lower() == lower_name:
                # Update key pair name
                self._key_pair = key_pair_name
                return

        # Key pair don't exists, creates it
        response = self._request(
            'CreateKeyPair', KeyPairName=self._key_pair)

        _utl.create_key_pair_file(self._key_pair, response['PrivateKeyBody'])

    def _init_security_group(self):
        """
        Initialize security group.
        """
        response = self._request('DescribeSecurityGroups')

        # Checks if security group exists
        lower_name = self._security_group.lower()
        for security_group in response['SecurityGroups']['SecurityGroup']:
            security_group_name = security_group['SecurityGroupName']
            if security_group_name.lower() == lower_name:
                # Update security group name
                self._security_group = security_group_name
                self._security_group_id = security_group['SecurityGroupId']
                break

        # Creates security group if not exists
        if not self._security_group_id:
            response = self._request(
                'CreateSecurityGroup',
                SecurityGroupName=self._security_group,
                Description=_utl.gen_msg('accelize_generated'))
            self._security_group_id = response['SecurityGroupId']

            _get_logger().info(_utl.gen_msg(
                'created_named', 'security group', self._security_group_id))

        # Adds host IP to security group if not already done
        public_ip = _utl.get_host_public_ip()
        rules = list()
        for port in self.ALLOW_PORTS:
            rules.append(dict(
                Priority=1, IpProtocol='tcp', PortRange='%s/%s' % (port, port),
                SourceCidrIp=public_ip))

        for rule in rules:
            self._request(
                'AuthorizeSecurityGroup',
                SecurityGroupId=self._security_group_id, **rule)

        _get_logger().info(
            _utl.gen_msg('authorized_ip', public_ip, self._security_group))

    def _init_role(self):
        """
        Initialize RAM role.

        This role allow to perform actions defined by policy.
        """
        assume_role_policy_document = _json.dumps({
            "Version": "1", "Statement": [{
                "Effect": "Allow",
                "Principal": {"Service": "ecs.aliyuncs.com"},
                "Action": "sts:AssumeRole"}]})

        if self._request(
                'CreateRole', domain='ram', RoleName=self._role,
                AssumeRolePolicyDocument=assume_role_policy_document,
                Description=_utl.gen_msg('accelize_generated'),
                error_code_ignore='EntityAlreadyExists'):

            _get_logger().info(_utl.gen_msg(
                'created_named', 'RAM role', self._role))

    def _init_policy(self):
        """
        Initialize RAM policy.

        This policy allow instance to:
            - Load FPGA bitstream.
            - Access to OSS buckets objects for read and write.
        """
        policy_document = _json.dumps({
            "Version": "1", "Statement": [
                # Grant FPGA access ()
                # TODO: Copied from "faasPolicy" check it,
                #       should be FAAS (aliyunsdkfaas)
                {"Effect": "Allow", "Resource": ["acs:ecs:*:*:*"],
                 "Action": ["ecs:DescribeInstances", "ecs:DescribeImages"]},
                {"Effect": "Allow", "Resource": ["acs:kms:*:*:*"],
                 "Action": ["kms:Decrypt", "kms:GenerateDataKey",
                            "kms:DescribeKey"]},
                # Grant OSS access
                {"Effect": "Allow", "Resource": ["acs:oss:*:*:*"],
                 "Action": ["oss:PutObject", "oss:GetObject", "oss:ListObjects",
                            "oss:ListBuckets"]}]})

        if self._request(
                'CreatePolicy', domain='ram', PolicyName=self._policy,
                PolicyDocument=policy_document,
                Description=_utl.gen_msg('accelize_generated'),
                error_code_ignore='EntityAlreadyExists'):

            _get_logger().info(_utl.gen_msg(
                'created_named', 'RAM policy', self._policy))

    def _attach_role_policy(self):
        """
        Attach RAM policy to RAM role.
        """
        if self._request(
                'AttachPolicyToRole', domain='ram', PolicyType='Custom',
                PolicyName=self._policy, RoleName=self._role,
                error_code_ignore='EntityAlreadyExists'):

            _get_logger().info(_utl.gen_msg(
                'attached_to', 'RAM policy', self._policy,
                'RAM role', self._role))

    def _create_instance(self):
        """
        Initialize and create instance.
        """
        futures = []
        with _ThreadPoolExecutor(max_workers=5) as executor:
            # Run configuration in parallel
            policy = executor.submit(self._init_policy)
            role = executor.submit(self._init_role)
            for method in (self._init_key_pair, self._init_security_group):
                futures.append(executor.submit(method))

            # Wait that role and policy are completed to attach them
            for future in _as_completed((policy, role)):
                future.result()
            futures.append(executor.submit(self._attach_role_policy))

        # Wait completion
        for future in _as_completed(futures):
            future.result()

    def _start_new_instance(self):
        """
        Starts a new instance.

        Returns:
            dict: Instance
            str: Instance ID
        """
        # Gets maximum Internet bandwidth
        response = self._request('DescribeBandwidthLimitation',
                                 InstanceType=self._instance_type)
        max_bandwidth = response['Bandwidths']['Bandwidth'][0]['Max']

        # Prepares args:
        kwargs = dict(
            ImageId=self._image_id, InstanceType=self._instance_type,
            SecurityGroupId=self._security_group_id,
            InstanceName=self._get_host_name(),
            Description=_utl.gen_msg('accelize_generated'),
            InternetMaxBandwidthOut=max_bandwidth,
            KeyPairName=self._key_pair, RamRoleName=self._role)

        # Handles user data
        user_data = self._user_data
        if user_data:
            # Needs to be in base64
            kwargs['UserData'] = _b64encode(user_data).decode()

        # Creates instance
        response = self._request('CreateInstance', **kwargs)
        instance_id = response['InstanceId']

        # Allocates public IP address
        self._instance_request(
            'AllocatePublicIpAddress', status_desc='allocating IP address',
            InstanceId=instance_id)

        # Starts instance
        self._instance_request(
            'StartInstance', status_desc='starting', InstanceId=instance_id)

        # Return basic instance description as instance and instance ID
        return {'InstanceId': instance_id}, instance_id

    def _start_existing_instance(self, status):
        """
        Starts a existing instance.

        Args:
            status (str): Status of the instance.
        """
        if status != self.STATUS_RUNNING:
            self._instance_request('StartInstance', status_desc='starting')

    def _terminate_instance(self):
        """
        Terminates and deletes instance.
        """
        # Needs to stop before delete, forces stop to make it faster
        self._pause_instance(force_stop=True)

        # Deletes instance
        self._instance_request('DeleteInstance', status_desc='deleting')

    def _pause_instance(self, force_stop=False):
        """
        Pauses instance.
        """
        if self._status() != self.STATUS_STOPPED:
            self._instance_request(
                'StopInstance', status_desc='stopping', ForceStop=force_stop)

    def _iter_hosts(self):
        """
        Iterates over accelerator hosts of current type.

        Returns:
            generator of dict: dicts contains attributes values of the host.
        """
        for instance in self._request(
                'DescribeInstances', Status=self.STATUS_RUNNING)[
                'Instances']['Instance']:

            host_name = instance['InstanceName']

            # Yields only matching accelerator instances
            if self._is_accelerator_host(host_name):
                yield dict(
                    instance_id=instance['InstanceId'],
                    instance_type=instance['InstanceType'],
                    private_ip=instance[
                        'VpcAttributes']['PrivateIpAddress']['IpAddress'][0],
                    public_ip=instance['PublicIpAddress']['IpAddress'][0],
                    host_name=host_name,
                    security_group=instance[
                        'SecurityGroupIds']['SecurityGroupId'][0],
                    image_id=instance['ImageId'],
                    key_pair=instance['KeyPairName'])
