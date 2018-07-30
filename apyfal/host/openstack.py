# coding=utf-8
"""OpenStack Nova"""
from contextlib import contextmanager as _contextmanager

from novaclient.client import Client as _Client
from novaclient.exceptions import (
    Unauthorized as _Unauthorized, ClientException as _ClientException)

from apyfal.host._csp import CSPHost as _CSPHost
import apyfal.exceptions as _exc
import apyfal._utilities as _utl
from apyfal._utilities import get_logger as _get_logger
import apyfal._utilities.openstack as _utl_openstack


@_contextmanager
def _exception_handler(to_raise=None, ignore=False, **exc_kwargs):
    """
    Context manager that catch OpenStack exceptions and raises
    Apyfal exceptions.

    Args:
        to_raise (apyfal.exception.AcceleratorException subclass):
            Exception to raise. self.RUNTIME if not specified.
        ignore (bool): If True, don't raises exception.
        exc_kwargs: Exception to raise arguments.
    """
    # Performs operation
    try:
        yield

    # Catch authentication exceptions
    except _Unauthorized as exception:
        raise _exc.HostAuthenticationException(exc=exception)

    # Catch specified exceptions
    except _ClientException as exception:
        # Raises Apyfal exception
        if not ignore:
            raise (to_raise or _exc.HostRuntimeException)(exc=exception, **exc_kwargs)


class OpenStackHost(_CSPHost):
    """OpenStack based CSP

    Args:
        host_type (str): Cloud service provider name. Default to "OpenStack".
        config (str or apyfal.configuration.Configuration or file-like object):
            Can be Configuration instance, apyfal.storage URL, paths, file-like object.
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
        instance_name_prefix (str): Prefix to add to instance name.
        host_ip (str): IP or URL address of an already existing AWS EC2 instance to use.
            If not specified, create a new instance.
        project_id (str): OpenStack Project
        auth_url (str): OpenStack auth-URL
        interface (str): OpenStack interface
        stop_mode (str or int): Define the "stop" method behavior.
            Default to 'term' if new instance, or 'keep' if already existing instance.
            See "stop_mode" property for more information and possible values.
        init_config (str or apyfal.configuration.Configuration or file-like object):
            Configuration file to pass to instance on initialization.
            This configuration file will be used as default for host side accelerator.
    """
    #: Provider name to use
    NAME = 'OpenStack'

    #: Instance status when running
    STATUS_RUNNING = 'ACTIVE'

    #: Instance status when stopped
    STATUS_STOPPED = 'PAUSED'

    #: Instance status when in error
    STATUS_ERROR = 'ERROR'

    # Default OpenStack auth-URL to use (str)
    OPENSTACK_AUTH_URL = None

    # Default Interface to use (str)
    OPENSTACK_INTERFACE = None

    _INFO_NAMES = _CSPHost._INFO_NAMES.copy()
    _INFO_NAMES.update({'_project_id', '_auth_url', '_interface'})

    _INIT_METHODS = list(_CSPHost._INIT_METHODS)
    _INIT_METHODS.append('_init_image')

    def __init__(self, project_id=None, auth_url=None, interface=None, **kwargs):
        _CSPHost.__init__(self, **kwargs)

        # OpenStack specific arguments
        section = self._config[self._config_section]
        self._project_id = project_id or section['project_id']

        self._auth_url = (
            auth_url or section['auth_url'] or
            self.OPENSTACK_AUTH_URL)

        self._interface = (
            interface or section['interface'] or
            self.OPENSTACK_INTERFACE)

        # Checks mandatory configuration values
        self._check_arguments('project_id', 'auth_url', 'interface')

        # Load session
        self._session = _Client(
            version='2', username=self._client_id, password=self._secret_id,
            project_id=self._project_id, auth_url=self._auth_url,
            region_name=self._region)

    def _check_credential(self):
        """
        Check CSP credentials.

        Raises:
            apyfal.exceptions.HostAuthenticationException:
                Authentication failed.
        """
        with _exception_handler():
            self._session.servers.list(detailed=False, limit=1)

    def _init_key_pair(self):
        """
        Initializes key pair.

        Returns:
            bool: True if reuses existing key
        """
        # Get key pair from CSP is exists
        key_pair_name = self._key_pair.lower()
        with _exception_handler(gen_msg=('no_find', "key pair")):
            for key_pair in self._session.keypairs.list():
                if key_pair.name.lower() == key_pair_name:
                    self._key_pair = key_pair.name
                    return

        # Create key pair if not exists
        with _exception_handler(gen_msg=('created_failed', "key pair")):
            key_pair = self._session.keypairs.create_keypair(name=self._key_pair)

        _utl.create_key_pair_file(self._key_pair, key_pair.private_key)
        _get_logger().info(_utl.gen_msg("created_named", "key pair", self._key_pair))

    def _init_security_group(self):
        """
        Initialize CSP security group.
        """
        # TODO: python-novaclient >= 8 don't support security groups
        # Needs to use neutronclient
        # https://github.com/gc3-uzh-ch/elasticluster/issues/425
        session = _utl_openstack.connect(
            region=self._region, auth_url=self._auth_url,
            client_id=self._client_id, secret_id=self._secret_id,
            project_id=self._project_id, interface=self._interface)

        # Create security group if not exists
        security_group = session.get_security_group(self._security_group)
        if security_group is None:
            security_group = session.create_security_group(
                self._security_group, _utl.gen_msg('accelize_generated'),
                project_id=self._project_id)
            _get_logger().info(_utl.gen_msg(
                'created_named', 'security group', security_group.name))

        # Verify rules associated to security group for host IP address
        public_ip = _utl.get_host_public_ip()

        # Create rule on SSH and HTTP
        for port in self.ALLOW_PORTS:
            try:
                session.create_security_group_rule(
                    security_group.id, port_range_min=port, port_range_max=port,
                    protocol="tcp", remote_ip_prefix=public_ip,
                    project_id=self._project_id)
            except _utl_openstack.SDKException:
                pass

        _get_logger().info(
            _utl.gen_msg('authorized_ip', public_ip, self._security_group))

    def _init_image(self):
        """
        Initializes image.
        """
        # Checks if image exists and get its name
        with _exception_handler(
                gen_msg=('unable_find_from', 'image', self._image_id, 'Accelize')):
            image = self._session.glance.find_image(self._image_id)
        try:
            self._image_name = image.name
        except AttributeError:
            raise _exc.HostConfigurationException(gen_msg=(
                'unable_find_from', 'image', self._image_id, 'Accelize'))

    def _init_flavor(self):
        """
        Initialize flavor
        """
        # Checks flavor exists and gets its ID
        # "instance_type" is name at this step
        with _exception_handler(
                to_raise=_exc.HostConfigurationException,
                gen_msg=('unable_find_from', 'flavor',
                         self._instance_type, self._host_type)):
            for flavor in self._session.flavors.list():
                if flavor.name.lower() == self._instance_type:
                    self._instance_type_name = flavor.name
                    self._instance_type = flavor.id

    def _create_instance(self):
        """
        Initializes and creates instance.
        """
        _CSPHost._create_instance(self)

        # Needs to run after others
        self._init_flavor()

    def _get_instance(self):
        """
        Returns current instance.

        Returns:
            object: Instance
        """
        # Try to find instance
        with _exception_handler(
                gen_msg=('no_instance_id', self._instance_id)):
            return self._session.servers.get(self._instance_id)

    def _get_public_ip(self):
        """
        Read current instance public IP from CSP instance.

        Returns:
            str: IP address
        """
        for address in list(self._get_instance().addresses.values())[0]:
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
        return self._get_instance().status

    def _start_new_instance(self):
        """
        Start a new instance.

        Returns:
            object: Instance
            str: Instance ID
        """
        with _exception_handler(gen_msg=('unable_to', "start")):
            image = self._session.glance.find_image(self._image_id)
            flavor = self._session.flavors.get(self._instance_type)
            instance = self._session.servers.create(
                name=self._get_instance_name(),
                image=image, flavor=flavor,
                key_name=self._key_pair,
                security_groups=[self._security_group],
                userdata=self._user_data)

        return instance, instance.id

    def _start_existing_instance(self, status):
        """
        Start a existing instance.

        Args:
            status (str): Status of the instance.
        """
        if status.lower() != self.STATUS_RUNNING:
            with _exception_handler(gen_msg=('unable_to', "start")):
                self._session.servers.start(self._instance)

    def _terminate_instance(self):
        """
        Terminate and delete instance.
        """
        with _exception_handler(gen_msg=('unable_to', "delete")):
            self._session.servers.force_delete(self._instance)

    def _pause_instance(self):
        """
        Pause instance.
        """
        with _exception_handler(gen_msg=('unable_to', "pause")):
            self._session.servers.pause(self._instance)
