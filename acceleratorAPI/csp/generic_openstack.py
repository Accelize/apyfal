# coding=utf-8
"""OpenStack based CSP"""

import keystoneauth1.exceptions.http as _keystoneauth_exceptions
import openstack as _openstack

import acceleratorAPI.csp as _csp
import acceleratorAPI.exceptions as _exc
import acceleratorAPI._utilities as _utl
from acceleratorAPI._utilities import get_logger as _get_logger


class OpenStackClass(_csp.CSPGenericClass):
    """Generic class for OpenStack based CSP

    Args:
        provider (str): Cloud service provider name.
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
        project_id:
        auth_url:
        interface:
        stop_mode (int): Define the "stop_instance" method behavior. See "stop_mode"
            property for more information and possible values.
        exit_instance_on_signal (bool): If True, exit CSP instances
            on OS exit signals. This may help to not have instance still running
            if Python interpreter is not exited properly. Note: this is provided for
            convenience and does not cover all exit case like process kill and
            may not work on all OS."""

    def __init__(self, **kwargs):
        _csp.CSPGenericClass.__init__(self, **kwargs)

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
        _get_logger().debug("Connection object created for CSP '%s'", self._provider)

    def check_credential(self):
        """
        Check CSP credentials.

        Raises:
            acceleratorAPI.exceptions.CSPAuthenticationException:
                Authentication failed.
        """
        try:
            list(self._session.network.networks())
        except _keystoneauth_exceptions.Unauthorized:
            raise _exc.CSPAuthenticationException()

    def _init_ssh_key(self):
        """
        Initialize CSP SSH key.
        """
        _get_logger().debug("Create or check if KeyPair %s exists", self._ssh_key)

        # Get key pair from CSP
        key_pair = self._session.compute.find_keypair(self._ssh_key, ignore_missing=True)

        # Use existing key
        if key_pair:
            _get_logger().info("KeyPair '%s' is already existing on %s.", key_pair.name, self._provider)
            return

        # Create key pair if not exists
        _get_logger().debug("Create KeyPair '%s'", self._ssh_key)
        key_pair = self._session.compute.create_keypair(name=self._ssh_key)

        _utl.create_ssh_key_file(self._ssh_key, key_pair.private_key)

    def _init_security_group(self):
        """
        Initialize CSP security group.
        """
        _get_logger().debug("Create or check if security group '%s' exists", self._security_group)

        # Create security group if not exists
        security_group = self._session.get_security_group(self._security_group)
        if security_group is None:
            security_group = self._session.create_security_group(
                self._security_group, "Generated by accelize API", project_id=self._project_id)
            _get_logger().info("Created security group: %s", security_group.name)

        else:
            _get_logger().info("Security group '%s' is already existing on %s.", self._security_group, self._provider)

        # Verify rules associated to security group for host IP address
        public_ip = _utl.get_host_public_ip()

        # Create rule on SSH
        try:
            self._session.create_security_group_rule(
                security_group.id, port_range_min=22, port_range_max=22, protocol="tcp", remote_ip_prefix=public_ip,
                project_id=self._project_id)

        except _openstack.exceptions.SDKException:
            pass

        # Create rule on HTTP
        try:
            self._session.create_security_group_rule(
                security_group.id, port_range_min=80, port_range_max=80, protocol="tcp", remote_ip_prefix=public_ip,
                project_id=self._project_id)
        except _openstack.exceptions.SDKException:
            pass

        _get_logger().info("Added in security group '%s': SSH and HTTP for IP %s.", self._security_group, public_ip)

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
            raise _exc.CSPInstanceException(
                "Could not find an instance with ID '%s' (%s)", self._instance_id, exception)

    def _get_instance_public_ip(self):
        """
        Read current instance public IP from CSP instance.

        Returns:
            str: IP address
        """
        for address in self._instance.addresses.values()[0]:
            if address['version'] == 4:
                return address['addr']
        raise _exc.CSPInstanceException("No instance address found")

    def _get_instance_status(self):
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
        self._init_ssh_key()
        self._init_security_group()

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
        # Get image
        image_id = accel_parameters_in_region['image']
        try:
            image = self._session.compute.find_image(image_id)
        except _openstack.exceptions.ResourceNotFound:
            raise _exc.CSPConfigurationException(
                ("Failed to get image information for CSP '%s':\n"
                 "The image '%s' is not available on your CSP account. "
                 "Please contact Accelize.") %
                (self._provider, image_id))
        else:
            _get_logger().debug("Set image '%s' with ID %s", image.name, image_id)

        # Get flavor
        flavor_name = accel_parameters_in_region['instancetype']
        try:
            instance_type = self._session.compute.find_flavor(flavor_name).id
        except _openstack.exceptions.ResourceNotFound:
            raise _exc.CSPConfigurationException(
                ("Failed to get flavor information for CSP '%s':\n"
                 "The flavor '%s' is not available in your CSP account. "
                 "Please contact you CSP to subscribe to this flavor.") %
                (self._provider, flavor_name))
        else:
            _get_logger().debug("Set flavor '%s' with ID %s", flavor_name, instance_type)

        return image_id, instance_type, self._config_env

    def _wait_instance_ready(self):
        """
        Wait until instance is ready.
        """
        # Waiting for the instance provisioning
        _get_logger().info("Waiting for the instance provisioning on %s...", self._provider)
        try:
            self._instance = self._session.compute.wait_for_server(self._instance)
        except _openstack.exceptions.SDKException as exception:
            raise _exc.CSPInstanceException("Instance exception: %s" % exception)

        # Check instance status
        state = self._get_instance_status()
        _get_logger().debug("Instance status: %s", state)
        if state.lower() == "error":
            self.stop_instance()
            raise _exc.CSPInstanceException("Instance has an invalid status: %s", state)

    def _start_new_instance(self):
        """
        Start a new instance.

        Returns:
            object: Instance
            str: Instance ID
        """
        instance = self._session.compute.create_server(
            name=self._accelerator, image_id=self._image_id, flavor_id=self._instance_type,
            key_name=self._ssh_key, security_groups=[{"name": self._security_group}])

        return instance, instance.id

    def _start_existing_instance(self, state):
        """
        Start a existing instance.

        Args:
            state (str): Status of the instance.
        """
        _get_logger().debug("Status of instance ID %s: %s", self._instance_id, state)
        if state.lower() != "active":
            self._session.start_server(self._instance)
        else:
            _get_logger().debug("Instance ID %s is already in '%s' state.", self._instance_id, state)

    def _log_instance_info(self):
        """
        Print some instance information in logger.
        """
        _get_logger().info("Region: %s", self._region)
        _get_logger().info("Public IP: %s", self.instance_ip)

    def _terminate_instance(self):
        """
        Terminate and delete instance.
        """
        if not self._session.delete_server(self._instance, wait=True):
            raise _exc.CSPInstanceException('Unable to delete instance.')

    def _pause_instance(self):
        """
        Pause instance.
        """
        # TODO: Implement pause instance support, actually terminates.
        self._terminate_instance()