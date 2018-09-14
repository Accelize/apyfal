# coding=utf-8
"""Cloud Service Providers"""

from abc import abstractmethod as _abstractmethod
from concurrent.futures import (ThreadPoolExecutor as _ThreadPoolExecutor,
                                as_completed as _as_completed)
import os.path as _os_path
from os import remove as _remove
from uuid import uuid4 as _uuid
try:
    # Python 2
    from StringIO import StringIO as _StringIO
except ImportError:
    # Python 3
    from io import StringIO as _StringIO

from apyfal.host import Host as _Host
import apyfal.configuration as _cfg
import apyfal.exceptions as _exc
import apyfal._utilities as _utl
import apyfal.storage as _srg
from apyfal._utilities import get_logger as _get_logger


class CSPHost(_Host):
    """This is base abstract class for all CSP classes.

    Args:
        host_type (str): Cloud service provider name.
        config (apyfal.configuration.Configuration, path-like object or file-like object):
            If not set, will search it in current working directory,
            in current user "home" folder. If none found, will use default
            configuration values.
            Path-like object can be path, URL or cloud object URL.
        client_id (str): CSP Access Key ID.
        secret_id (str): CSP Secret Access Key.
        region (str): CSP region. Needs a region supporting instances with FPGA
            devices.
        instance_type (str): CSP instance type. Default defined by accelerator.
        key_pair (str): CSP Key pair. Default to 'Accelize<HostName>KeyPair'.
        security_group: CSP Security group. Default to 'AccelizeSecurityGroup'.
        instance_id (str): Instance ID of an already existing CSP instance to
            use. If not specified, create a new instance.
        host_name_prefix (str): Prefix to add to instance name.
        host_ip (str): IP or URL address of an already existing CSP instance to
            use. If not specified, create a new instance.
        use_private_ip (bool): If True, on new instances,
            uses private IP instead of public IP as default host IP.
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
        ssl_cert_crt (path-like object or file-like object):
            Public ".crt" key file of the SSL ssl_cert_key used to provides
            HTTPS.
        ssl_cert_key (path-like object or file-like object):
            Private ".key" key file of the SSL ssl_cert_key used to provides
            HTTPS.
        ssl_cert_generate (bool): Generate a self signed ssl_cert_key.
            The ssl_cert_key and private key will be stored in files specified
            by "ssl_cert_crt" and "ssl_cert_key" (Or temporary certificates if
            not specified). Note that this ssl_cert_key is only safe if other
            client verify it by providing "ssl_cert_crt". No Certificate
            Authority are available to trust this ssl_cert_key.
    """
    #: Instance status when running
    STATUS_RUNNING = 'running'

    #: Instance status when stopped
    STATUS_STOPPED = 'stopped'

    #: Instance status when in error
    STATUS_ERROR = 'error'

    #: Allowed ports for instance access
    ALLOW_PORTS = {22, 80, 443}

    # Attributes returned as dict by "info" property
    _INFO_NAMES = _Host._INFO_NAMES.copy()
    _INFO_NAMES.update({
        'public_ip', 'private_ip', '_region', '_instance_type',
        '_key_pair', '_security_group', '_instance_id',
        '_instance_type_name', '_region_parameters', 'host_ip'})

    # Instance user home directory
    _HOME = '/home/centos'

    # "User data" initialized flag file
    _SH_FLAG = '/etc/nginx/.INITIALIZED'

    # Instance SSL ssl_cert_key
    _SSL_CERT_CRT = '/etc/nginx/apyfal_cert.crt'
    _SSL_CERT_KEY = '/etc/nginx/apyfal_cert.key'

    # User ssl_cert_key default storage
    _SSL_CERT_HOME_DIR = _os_path.join(_cfg.APYFAL_HOME, 'certificates')

    # Initialization methods
    _INIT_METHODS = ['_init_security_group', '_init_key_pair']

    # Value to show in repr
    # Python 2 don't .copy() on list
    _REPR = list(_Host._REPR)
    _REPR.append(('ID', '_instance_id'))

    def __init__(self, client_id=None, secret_id=None, region=None,
                 instance_type=None, key_pair=None, security_group=None,
                 instance_id=None, init_config=None, init_script=None,
                 ssl_cert_crt=None, ssl_cert_key=None, ssl_cert_generate=None,
                 use_private_ip=None,
                 **kwargs):
        _Host.__init__(self, **kwargs)

        # Default some attributes
        self._instance = None
        self._image_id = None
        self._image_name = None
        self._instance_type = None
        self._instance_type_name = None
        self._warn_keep_once = False

        # Read configuration from file
        section = self._config[self._config_section]
        self._client_id = client_id or section['client_id']
        self._secret_id = secret_id or section['secret_id']
        self._region = region or section['region']
        self._instance_type = instance_type or section['instance_type']
        self._instance_id = instance_id or section['instance_id']
        self._use_private_ip = (
            use_private_ip or section.get_literal('use_private_ip') or False)

        self._key_pair = (
            key_pair or section['key_pair'] or
            self._default_parameter_value('KeyPair', include_host=True))

        self._security_group = (
            security_group or section['security_group'] or
            self._default_parameter_value('SecurityGroup'))

        self.stop_mode = (
            kwargs.get('stop_mode') or section['stop_mode'] or
            ('keep' if instance_id or kwargs.get('host_ip') else 'term'))

        self._init_config = init_config or section['init_config']
        self._init_script = init_script or section['init_script']

        # Get SSL certificate
        self._ssl_cert_crt = ssl_cert_crt or section['ssl_cert_crt']
        self._ssl_cert_key = ssl_cert_key or section['ssl_cert_key']
        self._ssl_cert_generate = (
                ssl_cert_generate or section.get_literal('ssl_cert_generate')
                or False)

        # Defines SSL certificate path if not specified
        if self._ssl_cert_generate and not self._ssl_cert_crt:
            self._ssl_cert_crt = _os_path.join(
                self._SSL_CERT_HOME_DIR, str(_uuid()))
            self._ssl_cert_crt_tmp = True
        else:
            self._ssl_cert_crt_tmp = False
        if self._ssl_cert_generate and not self._ssl_cert_key:
            self._ssl_cert_key = _os_path.join(
                self._SSL_CERT_HOME_DIR, str(_uuid()))
            self._ssl_cert_key_tmp = True
        else:
            self._ssl_cert_key_tmp = False

        # Set HTTP/HTTPS as default depending on certificate
        if self._ssl_cert_crt:
            self._url = _utl.format_url(self._url, force_secure=True)

        # Checks mandatory configuration values
        self._check_arguments('region')

        if (self._client_id is None and
                self._instance_id is None and self._url is None):
            raise _exc.HostConfigurationException(
                "Need at least 'client_id', 'instance_id' or 'host_ip' "
                "argument. See documentation for more information.")

    @property
    def host_ip(self):
        """
        Host IP of the current instance. This may return public or private IP
        based on configuration.

        Returns:
            str: IP address

        Raises:
            apyfal.exceptions.HostRuntimeException:
                No instance from which get IP.
        """
        if self._use_private_ip:
            return self.private_ip
        return self.public_ip

    @property
    def public_ip(self):
        """
        Public IP of the current instance.

        Returns:
            str: IP address

        Raises:
            apyfal.exceptions.HostRuntimeException:
                No instance from which get IP.
        """
        if self._instance is None:
            raise _exc.HostRuntimeException(gen_msg='no_instance')
        return self._get_public_ip()

    @_abstractmethod
    def _get_public_ip(self):
        """
        Read current instance public IP from CSP instance.

        Returns:
            str: IP address
        """

    @property
    def key_pair(self):
        """
        SSH Key pair linked to this instance.

        Returns:
            str: Name of key pair.
        """
        return self._key_pair

    @property
    def private_ip(self):
        """
        Private IP of the current instance.

        Returns:
            str: IP address

        Raises:
            apyfal.exceptions.HostRuntimeException:
                No instance from which get IP.
        """
        if self._instance is None:
            raise _exc.HostRuntimeException(gen_msg='no_instance')
        return self._get_private_ip()

    @property
    def ssl_cert_crt(self):
        """
        SSL ssl_cert_key used.

        Returns:
            str: Path to SSL ssl_cert_key.
        """
        return self._ssl_cert_crt

    @_abstractmethod
    def _get_private_ip(self):
        """
        Read current instance private IP from CSP instance.

        Returns:
            str: IP address
        """

    @property
    def instance_id(self):
        """
        ID of the current instance.

        Returns:
            str: ID
        """
        return self._instance_id

    @_abstractmethod
    def _check_credential(self):
        """
        Check CSP credentials.

        Raises:
            apyfal.exceptions.HostAuthenticationException:
                Authentication failed.
        """

    def _status(self):
        """
        Returns current status of current instance.

        Returns:
            str: Status

        Raises:
            apyfal.exceptions.HostRuntimeException:
                No instance from which get status.
        """
        if self._instance_id is None:
            raise _exc.HostRuntimeException(gen_msg='no_instance')

        # Update instance
        self._instance = self._get_instance()

        if self._instance is None:
            raise _exc.HostRuntimeException(
                gen_msg=('no_instance_id', self._instance_id))

        # Read instance status
        return self._get_status()

    @_abstractmethod
    def _get_status(self):
        """
        Returns current status of current instance.

        Returns:
            str: Status
        """

    @_abstractmethod
    def _get_instance(self):
        """
        Returns current instance.

        Returns:
            object: Instance
        """

    @_abstractmethod
    def _init_key_pair(self):
        """
        Initializes key pair.

        Returns:
            bool: True if reuses existing key
        """

    @_abstractmethod
    def _init_security_group(self):
        """
        Initialize CSP security group.
        """

    def start(self, accelerator=None, accel_parameters=None, stop_mode=None):
        """
        Start instance if not already started. Create instance if necessary.

        Needs "accel_client" or "accel_parameters".

        Args:
            accelerator (str): Name of the accelerator.
            accel_parameters (dict): Can override parameters from accelerator
                client.
            stop_mode (str or int): See "stop_mode" property for more
                information.
        """
        # Updates stop mode
        self.stop_mode = stop_mode

        # Get parameters from accelerator
        self._set_accelerator_requirements(
            accelerator, accel_parameters)

        # Starts instance only if not already started
        if self._url is None:

            # Checks CSP credential
            self._check_credential()

            # Creates and starts instance if not exists
            if self.instance_id is None:
                _get_logger().info(
                    "Configuring %s instance...", self._host_type)

                try:
                    self._create_instance()
                except _exc.HostException as exception:
                    self._stop_silently(exception)
                    raise

                try:
                    self._instance, self._instance_id = (
                        self._start_new_instance())
                except _exc.HostException as exception:
                    self._stop_silently(exception)
                    raise

                _get_logger().info(_utl.gen_msg(
                    'created_named', 'instance', self._instance_id))

            # If exists, starts it directly
            else:
                status = self._status()
                self._start_existing_instance(status)

            # Waiting for instance provisioning
            _get_logger().info("Waiting instance provisioning...")
            try:
                self._wait_instance_ready()
            except _exc.HostException as exception:
                self._stop_silently(exception)
                raise

            # Update instance URL
            self._url = _utl.format_url(
                self.host_ip, force_secure=bool(self._ssl_cert_crt))

            # Waiting for the instance to boot
            _get_logger().info("Waiting instance boot...")
            self._wait_instance_boot()

            _get_logger().info("Instance ready")

        # If URL exists, checks if reachable
        elif not _utl.check_url(self._url):
            raise _exc.HostRuntimeException(
                gen_msg=('unable_reach_url', self._url))

    def _create_instance(self):
        """
        Initializes and creates instance.
        """
        # Run configuration in parallel
        futures = []
        with _ThreadPoolExecutor(
                max_workers=len(self._INIT_METHODS)) as executor:
            for method in self._INIT_METHODS:
                futures.append(executor.submit(getattr(self, method)))

        # Wait completion
        for future in _as_completed(futures):
            future.result()

    @_abstractmethod
    def _start_new_instance(self):
        """
        Starts a new instance.

        Returns:
            object: Instance
            str: Instance ID
        """

    @_abstractmethod
    def _start_existing_instance(self, status):
        """
        Starts a existing instance.

        Args:
            status (str): Status of the instance.
        """

    def _wait_instance_ready(self):
        """
        Waits until instance is ready.
        """
        # Waiting for the instance provisioning
        with _utl.Timeout(self.TIMEOUT) as timeout:
            while True:
                # Get instance status
                status = self._status()
                if status == self.STATUS_RUNNING:
                    return
                elif status == self.STATUS_ERROR:
                    raise _exc.HostRuntimeException(
                        gen_msg=('unable_to_status', "provision", status))
                elif timeout.reached():
                    raise _exc.HostRuntimeException(
                        gen_msg=('timeout_status', "provisioning", status))

    def _wait_instance_boot(self):
        """Waits until instance has booted and webservice is OK

        Raises:
            apyfal.exceptions.HostRuntimeException:
                Timeout while booting."""
        if not _utl.check_url(self._url, timeout=self.TIMEOUT):
            raise _exc.HostRuntimeException(gen_msg=('timeout', "boot"))

    def stop(self, stop_mode=None):
        """
        Stop instance accordingly with the current stop_mode.
        See "stop_mode" property for more information.

        Args:
            stop_mode (str or int): If not None, override current "stop_mode"
                value.
        """
        # No instance to stop (Avoid double call with __exit__ + __del__)
        if self._instance_id is None:
            return

        # Define stop mode
        if stop_mode is None:
            stop_mode = self._stop_mode

        # Keep instance alive
        if stop_mode == 'keep':
            if not self._warn_keep_once:
                self._warn_keep_once = True
                _get_logger().warning(
                    "Instance '%s' is still running" % self.instance_id)
            return

        # Checks if instance to stop
        try:
            # Force instance update
            self._instance = self._get_instance()

            # Checks status
            self._status()
        except _exc.HostRuntimeException:
            return

        # Terminates and delete instance completely
        if stop_mode == 'term':
            self._terminate_instance()
            _get_logger().info(
                "Instance '%s' has been terminated", self._instance_id)

        # Pauses instance and keep it alive
        else:
            self._pause_instance()
            _get_logger().info(
                "Instance '%s' has been stopped", self._instance_id)

        # Detaches from instance
        self._instance_id = None
        self._instance = None

        # Clean up temporary self signed certificates
        if self._ssl_cert_crt_tmp:
            _remove(self._ssl_cert_crt)

        if self._ssl_cert_key_tmp:
            _remove(self._ssl_cert_key)

    @_abstractmethod
    def _terminate_instance(self):
        """
        Terminates and deletes instance.
        """

    @_abstractmethod
    def _pause_instance(self):
        """
        Pauses instance.
        """

    def _stop_silently(self, exception):
        """
        Terminates and deletes instance ignoring errors.

        Args:
            exception(Exception): If provided, augment message
                of this exception with CSP help.
        """
        # Augment exception message
        if exception is not None:
            self._add_help_to_exception_message(exception)

        # Force stop instance, ignore exception if any
        try:
            self._terminate_instance()
        except _exc.HostException:
            pass

    def _set_accelerator_requirements(self, *args, **kwargs):
        """
        Configures instance with accelerator client parameters.

        Needs "accel_client" or "accel_parameters".

        Args:
            accelerator (str): Name of the accelerator
            accel_parameters (dict): Can override parameters from accelerator
                client.

        Raises:
            apyfal.exceptions.HostConfigurationException:
                Parameters are not valid.
        """
        _Host._set_accelerator_requirements(self, *args, **kwargs)

        # For CSP, config env are in a region sub category
        if self._region not in self._config_env.keys():
            raise _exc.HostConfigurationException(
                "Region '%s' is not supported. Available regions are: %s" % (
                    self._region, ', '.join(
                        region for region in self._config_env
                        if region != 'accelerator')))
        self._config_env = self._config_env[self._region]

        # Gets some CSP configuration values from environment
        self._image_id = self._config_env.pop('image')
        self._instance_type = self._config_env.pop('instancetype')

        # Sets AGFI backward compatibility
        try:
            self._config_env['AGFI'] = self._config_env['fpgaimage']
        except KeyError:
            pass

    @property
    def _user_data(self):
        """
        Generate a shell script to initialize instance.

        Returns:
            str: shell script.
        """
        # Initializes file with shebang
        commands = ["#!/usr/bin/env bash"]

        # Gets configuration file
        if self._init_config:
            config = (self._config if self._init_config is True else
                      self._init_config)

            # Write default configuration file
            stream = _StringIO()
            _cfg.create_configuration(config).write(stream)
            stream.seek(0)

            commands += ["cat << EOF > %s/accelerator.conf" % self._HOME,
                         stream.read(), "EOF\n"]

        # Gets SSL ssl_cert_key
        if self._ssl_cert_crt and self._ssl_cert_key:

            # Gets ssl_cert_key files
            if self._ssl_cert_generate:
                # Generates self signed wildcard ssl_cert_key because:
                # - No DNS host name available.
                # - Address IP is unknown at this step.
                from apyfal._certificates import self_signed_certificate
                ssl_cert_crt, ssl_cert_key = self_signed_certificate(
                    "*", common_name=self.host_name)

                # Creates temporary certificates dir
                if self._ssl_cert_key_tmp or self._ssl_cert_crt_tmp:
                    _utl.makedirs(self._SSL_CERT_HOME_DIR, exist_ok=True)

                # Saves certificates in files
                for path, content in ((self._ssl_cert_crt, ssl_cert_crt),
                                      (self._ssl_cert_key, ssl_cert_key)):
                    with _srg.open(path, 'wb') as src_file:
                        src_file.write(content)

            else:
                # Reads ssl_cert_key from files
                with _srg.open(self._ssl_cert_crt, 'rb') as src_file:
                    ssl_cert_crt = src_file.read()
                with _srg.open(self._ssl_cert_key, 'rb') as src_file:
                    ssl_cert_key = src_file.read()

            # Writes command
            for src, dst in ((ssl_cert_crt, self._SSL_CERT_CRT),
                             (ssl_cert_key, self._SSL_CERT_KEY)):
                commands += ["cat << EOF > %s" % dst, src.decode(), "EOF\n"]

        elif self._ssl_cert_crt or self._ssl_cert_key:
            # Needs both private and public keys
            raise _exc.HostConfigurationException(
                "Both 'ssl_cert_crt' and 'ssl_cert_key' are required")

        # Add initialization flag file
        commands.append('touch "%s"\n' % self._SH_FLAG)

        # Gets bash script
        if self._init_script:
            with _srg.open(self._init_script, 'rt') as script:
                lines = script.read().strip().splitlines()

            if lines[0].startswith("#!"):
                # Remove shebang
                lines = lines[1:]

            commands.extend(lines)

        return '\n'.join(commands).encode()
