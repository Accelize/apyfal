# coding=utf-8
"""OpenStack based CSP"""
# Absoluteimport required on Python 2 to avoid collision
# of this module with openstack-sdk package
from __future__ import absolute_import as _absolute_import

import keystoneauth1.exceptions.http as _keystoneauth_exceptions
import openstack as _openstack

from apyfal.host._csp import CSPHost as _CSPHost
import apyfal.configuration as _cfg
import apyfal.exceptions as _exc
import apyfal._utilities as _utl
from apyfal._utilities import get_logger as _get_logger


class OpenStackHost(_CSPHost):
    """OpenStack based CSP

    Args:
        host_type (str): Cloud service provider name. Default to "OpenStack".
        config (str or apyfal.configuration.Configuration): Configuration file path or instance.
            If not set, will search it in current working directory, in current
            user "home" folder. If none found, will use default configuration values.
        client_id (str): OpenStack Access Key ID.
        secret_id (str): OpenStack Secret Access Key.
        region (str): OpenStack region. Needs a region supporting instances with FPGA devices.
        instance_type (str): OpenStack Flavor. Default defined by accelerator.
        key_pair (str): OpenStack Key pair. Default to 'Accelize<HostName>KeyPair'.
        security_group: OpenStack Security group. Default to 'AccelizeSecurityGroup'.
        instance_id (str): Instance ID of an already existing OpenStack nova instance to use.
            If not specified, create a new instance.
        instance_ip (str): IP or URL address of an already existing OpenStack nova instance to use.
            If not specified, create a new instance.
        project_id (str): OpenStack Project
        auth_url (str): OpenStack auth-URL
        interface (str): OpenStack interface
        stop_mode (str or int): Define the "stop" method behavior.
            Default to 'term' if new instance, or 'keep' if already existing instance.
            See "stop_mode" property for more information and possible values.
        exit_host_on_signal (bool): If True, exit instance
            on OS exit signals. This may help to not have instance still running
            if Python interpreter is not exited properly. Note: this is provided for
            convenience and does not cover all exit case like process kill and
            may not work on all OS.
    """
    #: Provider name to use
    NAME = 'OpenStack'

    # Default OpenStack auth-URL to use (str)
    OPENSTACK_AUTH_URL = None

    # Default Interface to use (str)
    OPENSTACK_INTERFACE = None

    _INFO_NAMES = _CSPHost._INFO_NAMES.copy()
    _INFO_NAMES.update({'_project_id', '_auth_url', '_interface'})

    def __init__(self, config=None, project_id=None, auth_url=None, interface=None, **kwargs):
        config = _cfg.create_configuration(config)
        _CSPHost.__init__(self, config=config, **kwargs)

        # OpenStack specific arguments
        self._project_id = config.get_default(
            'host', 'project_id', overwrite=project_id)
        self._auth_url = config.get_default(
            'host', 'auth_url', overwrite=auth_url,
            default=self.OPENSTACK_AUTH_URL)
        self._interface = config.get_default(
            'host', 'interface', overwrite=interface,
            default=self.OPENSTACK_INTERFACE)

        # Checks mandatory configuration values
        self._check_arguments('project_id', 'auth_url', 'interface')

        # Load session
        self._session = _openstack.connection.Connection(
            region_name=self._region,
            auth=dict(
                auth_url=self._auth_url,
                username=self._client_id,
                password=self._secret_id,
                project_id=self._project_id
            ),
            compute_api_version='2',
            identity_interface=self._interface
        )

    def _check_credential(self):
        """
        Check CSP credentials.

        Raises:
            apyfal.exceptions.HostAuthenticationException:
                Authentication failed.
        """
        try:
            list(self._session.network.networks())
        except (_keystoneauth_exceptions.Unauthorized,
                _openstack.exceptions.SDKException) as exception:
            raise _exc.HostAuthenticationException(exc=exception)

    def _init_key_pair(self):
        """
        Initializes key pair.

        Returns:
            bool: True if reuses existing key
        """
        # Get key pair from CSP
        try:
            key_pair = self._session.compute.find_keypair(self._key_pair, ignore_missing=True)
        except _openstack.exceptions.SDKException as exception:
            raise _exc.HostRuntimeException(
                gen_msg=('no_find', "key pair"), exc=exception)

        # Use existing key
        if key_pair:
            return True

        # Create key pair if not exists
        try:
            key_pair = self._session.compute.create_keypair(name=self._key_pair)
        except _openstack.exceptions.SDKException as exception:
            raise _exc.HostRuntimeException(
                gen_msg=('created_failed', "key pair"), exc=exception)

        _utl.create_key_pair_file(self._key_pair, key_pair.private_key)

        return False

    def _init_security_group(self):
        """
        Initialize CSP security group.
        """
        # Create security group if not exists
        security_group = self._session.get_security_group(self._security_group)
        if security_group is None:
            security_group = self._session.create_security_group(
                self._security_group, _utl.gen_msg('accelize_generated'),
                project_id=self._project_id)
            _get_logger().info(_utl.gen_msg(
                'created_named', 'security group', security_group.name))

        # Verify rules associated to security group for host IP address
        public_ip = _utl.get_host_public_ip()

        # Create rule on SSH
        try:
            self._session.create_security_group_rule(
                security_group.id, port_range_min=22, port_range_max=22,
                protocol="tcp", remote_ip_prefix=public_ip,
                project_id=self._project_id)
        except _openstack.exceptions.SDKException:
            pass

        # Create rule on HTTP
        try:
            self._session.create_security_group_rule(
                security_group.id, port_range_min=80, port_range_max=80,
                protocol="tcp", remote_ip_prefix=public_ip,
                project_id=self._project_id)
        except _openstack.exceptions.SDKException:
            pass

        _get_logger().info(
            _utl.gen_msg('authorized_ip', public_ip, self._security_group))

    def _get_instance(self):
        """
        Returns current instance.

        Returns:
            object: Instance
        """
        # Try to find instance
        try:
            return self._session.get_server(self._instance_id)

        # Instance not found
        except _openstack.exceptions.SDKException as exception:
            raise _exc.HostRuntimeException(
                gen_msg=('no_instance_id', self._instance_id),
                exc=exception)

    def _get_public_ip(self):
        """
        Read current instance public IP from CSP instance.

        Returns:
            str: IP address
        """
        for address in list(self._instance.addresses.values())[0]:
            if address['version'] == 4:
                return address['addr']
        raise _exc.HostRuntimeException(gen_msg='no_instance_ip')

    def _get_private_ip(self):
        """
        Read current instance private IP from CSP instance.

        Returns:
            str: IP address
        """
        return ''

    def _get_status(self):
        """
        Returns current status of current instance.

        Returns:
            str: Status
        """
        return self._instance.status

    def _create_instance(self):
        """
        Initialize and create instance.
        """
        self._init_security_group()

    def _get_image_id_from_region(self, accel_parameters_in_region):
        """
        Read accelerator parameters and get image id.

        Args:
            accel_parameters_in_region (dict): AcceleratorClient parameters
                for the current CSP region.

        Returns:
            str: image_id
        """
        # Gets image
        image_id = _CSPHost._get_image_id_from_region(
            accel_parameters_in_region)

        # Checks if image exists and get its name
        try:
            image = self._session.compute.find_image(image_id)
        except _openstack.exceptions.ResourceNotFound:
            raise _exc.HostConfigurationException(gen_msg=(
                'unable_find_from', 'image', image_id, 'Accelize'))
        else:
            try:
                self._image_name = image.name
            except AttributeError:
                raise _exc.HostConfigurationException(gen_msg=(
                    'unable_find_from', 'image', image_id, 'Accelize'))

        return image_id

    def _get_instance_type_from_region(self, accel_parameters_in_region):
        """
        Read accelerator parameters and instance type.

        Args:
            accel_parameters_in_region (dict): AcceleratorClient parameters
                for the current CSP region.

        Returns:
            str: instance_type
        """
        # Get instance type (flavor)
        self._instance_type_name = _CSPHost._get_instance_type_from_region(
            accel_parameters_in_region)
        try:
            instance_type = self._session.compute.find_flavor(
                self._instance_type_name).id
        except _openstack.exceptions.ResourceNotFound:
            raise _exc.HostConfigurationException(gen_msg=(
                'unable_find_from', 'flavor',
                self._instance_type_name, self._host_type))

        return instance_type

    def _wait_instance_ready(self):
        """
        Wait until instance is ready.
        """
        # Waiting for the instance provisioning
        try:
            self._instance = self._session.compute.wait_for_server(self._instance)
        except _openstack.exceptions.SDKException as exception:
            self._instance = self._get_instance()
            try:
                msg = self._instance.fault.message
            except AttributeError:
                msg = exception
            raise _exc.HostRuntimeException(exc=msg)

        # Check instance status
        status = self._get_status()
        if status.lower() == "error":
            self.stop()
            raise _exc.HostRuntimeException(
                gen_msg=('unable_to_status', "initialize", status))

    def _start_new_instance(self):
        """
        Start a new instance.

        Returns:
            object: Instance
            str: Instance ID
        """
        try:
            instance = self._session.compute.create_server(
                name=self._get_instance_name(),
                image_id=self._image_id, flavor_id=self._instance_type,
                key_name=self._key_pair,
                security_groups=[{"name": self._security_group}])
        except _openstack.exceptions.SDKException as exception:
            raise _exc.HostRuntimeException(
                gen_msg=('unable_to', "start"), exc=exception)

        return instance, instance.id

    def _start_existing_instance(self, status):
        """
        Start a existing instance.

        Args:
            status (str): Status of the instance.
        """
        if status.lower() != "active":
            try:
                self._session.start_server(self._instance)
            except _openstack.exceptions.SDKException as exception:
                raise _exc.HostRuntimeException(
                    gen_msg=('unable_to', "start"), exc=exception)

    def _terminate_instance(self):
        """
        Terminate and delete instance.
        """
        try:
            if not self._session.delete_server(self._instance, wait=True):
                raise _exc.HostRuntimeException(_utl.gen_msg('unable_to', "delete"))
        except _openstack.exceptions.SDKException as exception:
            raise _exc.HostRuntimeException(
                gen_msg=('unable_to', "delete"), exc=exception)

    def _pause_instance(self):
        """
        Pause instance.
        """
        # TODO: Implement pause instance support, actually terminates. shutdown ?
        self._terminate_instance()
