# coding=utf-8
"""OpenStack Nova"""
from contextlib import contextmanager as _contextmanager

from novaclient.client import Client as _NovaClient
from neutronclient.v2_0.client import Client as _NeutronClient
import novaclient.exceptions as _nova_exc
import neutronclient.common.exceptions as _neutron_exc

from apyfal.host._csp import CSPHost as _CSPHost
import apyfal.exceptions as _exc
import apyfal._utilities as _utl
from apyfal._utilities import get_logger as _get_logger


@_contextmanager
def _exception_handler(to_raise=None, filter_error_codes=None, **exc_kwargs):
    """
    Context manager that catch OpenStack exceptions and raises
    Apyfal exceptions.

    Args:
        to_raise (apyfal.exception.AcceleratorException subclass):
            Exception to raise. self.RUNTIME if not specified.
        filter_error_codes (tuple):
                Don't raise exception if error code in this argument.
        exc_kwargs: Exception to raise arguments.
    """
    # Performs operation
    try:
        yield

    # Catch authentication exceptions
    except (_nova_exc.Unauthorized, _neutron_exc.Unauthorized) as exception:
        raise _exc.HostAuthenticationException(exc=exception)

    # Catch specified exceptions
    except (_nova_exc.ClientException,
            _neutron_exc.NeutronClientException) as exception:
        error_code = None
        for attr_name in ('code', 'status_code'):
            if hasattr(exception, attr_name):
                error_code = getattr(exception, attr_name)
                break

        if filter_error_codes is None:
            filter_error_codes = ()

        # Raises Apyfal exception
        if error_code not in filter_error_codes:
            raise (to_raise or _exc.HostRuntimeException)(
                exc=exception, **exc_kwargs)


class OpenStackHost(_CSPHost):
    """OpenStack based CSP

    Args:
        host_type (str): Cloud service provider name. Default to "OpenStack".
        config (apyfal.configuration.Configuration, path-like object or file-like object):
            If not set, will search it in current working directory,
            in current user "home" folder. If none found, will use default
            configuration values.
            Path-like object can be path, URL or cloud object URL.
        client_id (str): OpenStack Access Key ID.
        secret_id (str): OpenStack Secret Access Key.
        region (str): OpenStack region. Needs a region supporting instances with
            FPGA devices.
        instance_type (str): OpenStack Flavor. Default defined by accelerator.
        key_pair (str): OpenStack Key pair.
            Default to 'Accelize<HostName>KeyPair'.
        security_group: OpenStack Security group.
            Default to 'AccelizeSecurityGroup'.
        instance_id (str): Instance ID of an already existing OpenStack nova
            instance to use. If not specified, create a new instance.
        host_name_prefix (str): Prefix to add to instance name.
            Also used as value of the "Apyfal" metadata.
        host_ip (str): IP or URL address of an already existing OpenStack nova
            instance to use. If not specified, create a new instance.
        use_private_ip (bool): If True, on new instances,
            uses private IP instead of public IP as default host IP.
        project_id (str): OpenStack Project
        auth_url (str): OpenStack auth-URL
        stop_mode (str or int): Define the "stop" method behavior.
            Default to 'term' if new instance, or 'keep' if already existing
            instance. See "stop_mode" property for more information and possible
            values.
        init_config (bool or apyfal.configuration.Configuration, path-like object or file-like object):
            Configuration file to pass to instance on
            initialization. This configuration file will be used as default for
            host side accelerator.
            If value is True, use 'config' configuration.
            If value is a configuration use this configuration.
            If value is None or False, don't passe any configuration file
            (This is default behavior).
        init_script (path-like object or file-like object): A bash script
            to execute on instance startup.
        ssl_cert_crt (path-like object or file-like object or bool):
            Public ".crt" key file of the SSL ssl_cert_key used to provides
            HTTPS.
            If not specified, uses already generated certificate if found.
            If False, disable HTTPS.
        ssl_cert_key (path-like object or file-like object):
            Private ".key" key file of the SSL ssl_cert_key used to provides
            HTTPS.
            If not specified, uses already generated key if found.
        ssl_cert_generate (bool): Generate a self signed ssl_cert_key.
            The ssl_cert_key and private key will be stored in files specified
            by "ssl_cert_crt" and "ssl_cert_key" (Or temporary certificates if
            not specified). Note that this ssl_cert_key is only safe if other
            client verify it by providing "ssl_cert_crt". No Certificate
            Authority are available to trust this ssl_cert_key.
        nova_client_kwargs (dict): Extra keyword arguments for
            novaclient.client.Client.
        nova_client_create_server_kwargs (dict): Extra Keyword arguments for
            novaclient.servers.ServerManager.create.
        neutron_client_kwargs (dict): Extra keyword arguments for
            neutronclient.client.Client. By default, neutron client
            inherits from nova client session.
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

    _INFO_NAMES = _CSPHost._INFO_NAMES.copy()
    _INFO_NAMES.update({'_project_id', '_auth_url'})

    _INIT_METHODS = list(_CSPHost._INIT_METHODS)
    _INIT_METHODS.append('_init_image')

    def __init__(self, project_id=None, auth_url=None,
                 nova_client_kwargs=None, nova_client_create_server_kwargs=None,
                 neutron_client_kwargs=None, **kwargs):
        _CSPHost.__init__(self, **kwargs)

        # OpenStack specific arguments
        section = self._config[self._config_section]
        self._project_id = project_id or section['project_id']

        self._auth_url = (
            auth_url or section['auth_url'] or
            self.OPENSTACK_AUTH_URL)

        self._nova_client_kwargs = (
            nova_client_kwargs or
            section.get_literal('nova_client_kwargs') or dict())
        self._nova_client_create_server_kwargs = (
            nova_client_create_server_kwargs or
            section.get_literal('nova_client_create_server_kwargs') or dict())
        self._neutron_client_kwargs = (
            neutron_client_kwargs or
            section.get_literal('neutron_client_kwargs') or dict())

        # Checks mandatory configuration values
        self._check_arguments('project_id', 'auth_url')

    @property
    @_utl.memoizedmethod
    def _nova_client(self):
        """
        Return Nova client

        Returns:
            novaclient.client.Client: Nova client
        """
        kwargs = dict(
            version='2', username=self._client_id, password=self._secret_id,
            project_id=self._project_id, auth_url=self._auth_url,
            region_name=self._region)
        kwargs.update(self._nova_client_kwargs)
        return _NovaClient(**kwargs)

    @property
    @_utl.memoizedmethod
    def _neutron_client(self):
        """
        Return Neutron client

        Returns:
            neutronclient.client.Client: Neutron client
        """
        kwargs = dict(session=self._nova_client.client.session,
                      region_name=self._region)
        kwargs.update(self._neutron_client_kwargs)
        return _NeutronClient(**kwargs)

    def _check_credential(self):
        """
        Check CSP credentials.

        Raises:
            apyfal.exceptions.HostAuthenticationException:
                Authentication failed.
        """
        with _exception_handler():
            self._nova_client.servers.list(detailed=False, limit=1)

    def _init_key_pair(self):
        """
        Initializes key pair.

        Returns:
            bool: True if reuses existing key
        """
        # Get key pair from CSP is exists
        key_pair_name = self._key_pair.lower()
        with _exception_handler(gen_msg=('no_find', "key pair")):
            for key_pair in self._nova_client.keypairs.list():
                if key_pair.name.lower() == key_pair_name:
                    self._key_pair = key_pair.name
                    return

        # Create key pair if not exists
        with _exception_handler(gen_msg=('created_failed', "key pair")):
            key_pair = self._nova_client.keypairs.create_keypair(
                name=self._key_pair)

        _utl.create_key_pair_file(self._key_pair, key_pair.private_key)
        _get_logger().debug(_utl.gen_msg(
            "created_named", "key pair", self._key_pair))

    def _init_security_group(self):
        """
        Initialize security group.
        """
        # Checks if security group exists
        security_group_id = None
        security_group_name = self._security_group.lower()
        with _exception_handler(gen_msg=('no_find', "security groups")):
            for security_group in self._neutron_client.list_security_groups(
                    )['security_groups']:
                if security_group['name'].lower() == security_group_name:
                    self._security_group = security_group['name']
                    security_group_id = security_group['id']

        # Create security group if not exists
        if security_group_id is None:
            with _exception_handler(gen_msg=(
                    'created_failed', "security groups")):
                security_group_id = self._neutron_client.create_security_group({
                    'security_group': {
                        'name': self._security_group,
                        'description': _utl.gen_msg('accelize_generated'),
                    }})['security_group']['id']

            _get_logger().debug(_utl.gen_msg(
                'created_named', 'security group', self._security_group))

        # Verify rules associated to security group for host IP address
        public_ip = _utl.get_host_public_ip()

        # Create rule on SSH and HTTP
        for port in self.ALLOW_PORTS:
            with _exception_handler(filter_error_codes=(409,)):
                self._neutron_client.create_security_group_rule(
                   {'security_group_rule': {
                       'direction': 'ingress', 'port_range_min': str(port),
                       'port_range_max': str(port),
                       'remote_ip_prefix': public_ip,
                       'protocol': 'tcp',
                       'security_group_id': security_group_id}})

        _get_logger().debug(
            _utl.gen_msg('authorized_ip', public_ip, self._security_group))

    def _init_image(self):
        """
        Initializes image.
        """
        # Checks if image exists and get its name
        with _exception_handler(gen_msg=(
                'unable_find_from', 'image', self._image_id, 'Accelize')):
            image = self._nova_client.glance.find_image(self._image_id)
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
            for flavor in self._nova_client.flavors.list():
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
        with _exception_handler(gen_msg=(
                'no_instance_id', self._instance_id)):
            return self._nova_client.servers.get(self._instance_id)

    def _get_public_ip(self):
        """
        Read current instance public IP from CSP instance.

        Returns:
            str: IP address
        """
        with _utl.Timeout(self.TIMEOUT, sleep=self._TIMEOUT_SLEEP) as timeout:
            while True:
                for address in list(
                        self._get_instance().addresses.values())[0]:
                    if address['version'] == 4:
                        return address['addr']
                if timeout.reached():
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

    def _wait_instance_ready(self):
        """
        Waits until instance is ready.
        """
        try:
            _CSPHost._wait_instance_ready(self)
        except _exc.HostException as exception:
            # Get extra information about error if possible
            try:
                raise _exc.HostRuntimeException(
                    exception.args[0],
                    exc=self._get_instance().fault['message'])

            # If not extra information, re raise previous error
            except (AttributeError, _nova_exc.ClientException):
                raise exception

    def _start_new_instance(self):
        """
        Start a new instance.

        Returns:
            object: Instance
            str: Instance ID
        """
        kwargs = dict(
            name=self._get_host_name(), key_name=self._key_pair,
            security_groups=[self._security_group],
            userdata=self._user_data, meta={'Apyfal': self._get_tag()})

        with _exception_handler(gen_msg=('unable_to', "start")):
            kwargs["image"] = self._nova_client.glance.find_image(
                self._image_id)
            kwargs["flavor"] = self._nova_client.flavors.get(
                self._instance_type)

            _utl.recursive_update(
                kwargs, self._nova_client_create_server_kwargs)

            instance = self._nova_client.servers.create(**kwargs)

        return instance, instance.id

    def _start_existing_instance(self, status):
        """
        Start a existing instance.

        Args:
            status (str): Status of the instance.
        """
        if status == self.STATUS_RUNNING:
            return

        with _exception_handler(gen_msg=('unable_to', "start")):
            if status == self.STATUS_STOPPED:
                self._nova_client.servers.unpause(self._instance)
            else:
                self._nova_client.servers.start(self._instance)

    def _terminate_instance(self):
        """
        Terminate and delete instance.
        """
        with _exception_handler(gen_msg=('unable_to', "delete"),
                                filter_error_codes=(404,)):
            self._nova_client.servers.force_delete(self._instance)

    def _pause_instance(self):
        """
        Pause instance.
        """
        with _exception_handler(gen_msg=('unable_to', "pause")):
            self._nova_client.servers.pause(self._instance)

    def _iter_hosts(self):
        """
        Iterates over accelerator hosts of current type.

        Returns:
            generator of dict: dicts contains attributes values of the host.
        """
        with _exception_handler():
            for instance in self._nova_client.servers.list(
                    search_opts={'status': self.STATUS_RUNNING}):
                host_name = instance.name

                # Yields only matching accelerator instances
                if self._is_accelerator_host(host_name):
                    yield dict(
                        instance_id=instance.id,
                        instance_type=instance.flavor['id'],
                        public_ip=[
                            address['addr'] for address in
                            list(instance.addresses.values())[0]
                            if address['version'] == 4][0],
                        host_name=host_name,
                        security_group=instance.security_groups[0]['name'],
                        image_id=instance.image['id'],
                        key_pair=instance.key_name)
