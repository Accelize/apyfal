# coding=utf-8
"""Cloud Service Providers"""

from abc import abstractmethod as _abstractmethod
from contextlib import contextmanager as _contextmanager
from concurrent.futures import (ThreadPoolExecutor as _ThreadPoolExecutor,
                                as_completed as _as_completed)
import os.path as _os_path
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
            Also used as value of the "Apyfal" tag.
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
            by "ssl_cert_crt" and "ssl_cert_key".
            if ssl_cert_crt" and "ssl_cert_key" are not specified, a
            certificate is create in user home if no existing certificate are
            found.
            Note that this ssl_cert_key is only safe if other
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

    # Host user home directory
    _HOME = '/home/centos'

    # "User data" initialized flag file
    _SH_FLAG = '/etc/nginx/.INITIALIZED'

    # Host SSL ssl_cert_key
    _SSL_CERT_CRT = '/etc/nginx/apyfal_cert.crt'
    _SSL_CERT_KEY = '/etc/nginx/apyfal_cert.key'

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
        section = self._config[self._config_section]

        # CSP
        self._client_id = client_id or section['client_id']
        self._secret_id = secret_id or section['secret_id']
        self._region = region or section['region']

        # Instance data
        self._instance_type = instance_type or section['instance_type']
        self._instance_id = instance_id or section['instance_id']
        self._use_private_ip = (
            use_private_ip or section.get_literal('use_private_ip') or False)

        # Security
        self._key_pair = (
            key_pair or section['key_pair'] or
            self._default_parameter_value('KeyPair', include_host=True))

        self._security_group = (
            security_group or section['security_group'] or
            self._default_parameter_value('SecurityGroup'))

        # Instance stop on "stop", "with" exit or garbage collection
        self.stop_mode = (
            kwargs.get('stop_mode') or section['stop_mode'] or
            ('keep' if instance_id or kwargs.get('host_ip') else 'term'))

        # User data
        self._init_config = init_config or section['init_config']
        self._init_script = init_script or section['init_script']

        # Gets SSL certificate
        self._ssl_cert_key, self._ssl_cert_crt, self._ssl_cert_generate = \
            self._get_certificates_arguments(
                ssl_cert_key, ssl_cert_crt, ssl_cert_generate)
        self._init_certificates()

        # Checks mandatory configuration values
        self._check_arguments('region')
        self._check_host_id_arguments()

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
        self._set_accelerator_requirements(accelerator, accel_parameters)

        # Starts instance only if not already started
        if self._url is None:

            # Checks CSP credential
            self._check_credential()

            # Creates and starts instance if not exists
            if self.instance_id is None:
                _get_logger().info(
                    "Configuring host on %s instance...", self._host_type)

                with self._stop_silently_on_exception():
                    self._create_instance()

                with self._stop_silently_on_exception():
                    self._instance, self._instance_id = \
                        self._start_new_instance()

                _get_logger().debug(_utl.gen_msg(
                    'created_named', 'instance', self._instance_id))

            # If exists, starts it directly
            else:
                self._start_existing_instance(self._status())

            # Waiting for instance provisioning
            with self._stop_silently_on_exception():
                self._wait_instance_ready()

            # Update instance URL
            self._url = _utl.format_url(
                self.host_ip, force_secure=bool(self._ssl_cert_crt))

            # Waiting for the instance to boot
            self._wait_instance_boot()

            _get_logger().info("Host ready")

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
        warned = False
        # Waiting for the instance provisioning
        with _utl.Timeout(self.TIMEOUT, sleep=self._TIMEOUT_SLEEP) as timeout:
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

                elif not warned:
                    # Avoid to show message if already booted
                    warned = True
                    _get_logger().info("Waiting instance provisioning...")

    def _wait_instance_boot(self):
        """Waits until instance has booted and webservice is OK

        Raises:
            apyfal.exceptions.HostRuntimeException:
                Timeout while booting."""
        if _utl.check_url(self._url):
            # Avoid to show message if already booted
            return

        _get_logger().info("Waiting instance boot...")
        if not _utl.check_url(self._url, timeout=self.TIMEOUT,
                              sleep=self._TIMEOUT_SLEEP):
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
                _get_logger().info(
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

    @_contextmanager
    def _stop_silently_on_exception(self):
        """
        Terminates and deletes instance ignoring errors.
        """
        try:
            yield

        except _exc.HostException as exception:
            # Augment exception
            self._add_help_to_exception_message(exception)

            # Force stop instance, ignore error if any
            try:
                self._terminate_instance()
            except _exc.HostException:
                pass

            # Re-raise exception
            raise

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
        self._cat_config_file(commands)

        # Gets SSL ssl_cert_key
        if self._ssl_cert_crt and self._ssl_cert_key:
            self._cat_ssl_cert_files(commands)

        elif self._ssl_cert_crt or self._ssl_cert_key:
            # Needs both private and public keys
            raise _exc.HostConfigurationException(
                "Both 'ssl_cert_crt' and 'ssl_cert_key' are required")

        # Add initialization flag file
        commands.append('touch "%s"\n' % self._SH_FLAG)

        # Gets user bash script
        self._extend_init_script(commands)

        # Return final script
        return '\n'.join(commands).encode()

    def _extend_init_script(self, commands):
        """
        Update command with user init script.

        Args:
            commands (list of str): Commands
        """
        if not self._init_script:
            return

        with _srg.open(self._init_script, 'rt') as script:
            # Get lines and remove shebang
            commands.extend([
                line for line in script.read().strip().splitlines()
                if not line.startswith("#!")])

    def _cat_config_file(self, commands):
        """
        Update command with cat of configuration file.

        Args:
            commands (list of str): Commands
        """
        if not self._init_config:
            return

        config = (self._config if self._init_config is True else
                  self._init_config)

        # Write default configuration file
        stream = _StringIO()
        _cfg.create_configuration(config).write(stream)
        stream.seek(0)
        commands += ["cat << EOF > %s/accelerator.conf" % self._HOME,
                     stream.read(), "EOF\n"]

    def _cat_ssl_cert_files(self, commands):
        """
        Update command with cat of certificate files.

        Args:
            commands (list of str): Commands
        """
        # Gets ssl_cert_key files
        if self._ssl_cert_generate:
            from apyfal._certificates import create_wildcard_certificate
            ssl_cert_crt, ssl_cert_key = create_wildcard_certificate(
                common_name=self.host_name)

            # Saves certificates in files
            for path, content in ((self._ssl_cert_crt, ssl_cert_crt),
                                  (self._ssl_cert_key, ssl_cert_key)):
                with _srg.open(path, 'wb') as src_file:
                    src_file.write(content)

        else:
            # Reads ssl_cert_key from files
            with _srg.open(self._ssl_cert_crt) as src_file:
                ssl_cert_crt = src_file.read()
            with _srg.open(self._ssl_cert_key) as src_file:
                ssl_cert_key = src_file.read()

        # Writes command
        for src, dst in ((ssl_cert_crt, self._SSL_CERT_CRT),
                         (ssl_cert_key, self._SSL_CERT_KEY)):
            commands += ["cat << EOF > %s" % dst, src.decode(), "EOF\n"]

    def _get_tag(self):
        """
        Returns "Apyfal" tag value.

        Returns
            str: tag value
        """
        return self._host_name_prefix or 'Apyfal'

    def _get_certificates_arguments(
            self, ssl_cert_key, ssl_cert_crt, ssl_cert_generate):
        """
        Get certificates related arguments.

        Args:
            ssl_cert_key (str):
            ssl_cert_crt (str or bool):
            ssl_cert_generate (bool):

        Returns:
            tuple: ssl_cert_key, ssl_cert_crt, ssl_cert_generate
        """
        section = self._config[self._config_section]

        # Private key
        ssl_cert_key = ssl_cert_key or section['ssl_cert_key']

        # Public certificate
        if ssl_cert_crt is not False:
            ssl_cert_crt = ssl_cert_crt or section.get_literal('ssl_cert_crt')

        # Generated certificate
        ssl_cert_generate = (
            ssl_cert_generate or section.get_literal('ssl_cert_generate')
            or False)

        return ssl_cert_key, ssl_cert_crt, ssl_cert_generate

    def _init_certificates(self):
        """
        Initializes certificates paths
        """
        # Defines SSL certificate path if not specified
        if self._ssl_cert_generate and self._ssl_cert_crt is not False:

            if not self._ssl_cert_crt:
                self._ssl_cert_crt = _cfg.APYFAL_CERT_CRT
                generated = True
                exists = _os_path.isfile(self._ssl_cert_crt)
            else:
                generated = False
                exists = False

            if not self._ssl_cert_key:
                self._ssl_cert_key = _cfg.APYFAL_CERT_KEY
                generated = True
                exists &= _os_path.isfile(self._ssl_cert_key)

            if exists:
                # Files already exists, don't need to generate them
                self._ssl_cert_generate = False

            elif generated:
                # Files needs to be generated, ensures directories exists
                for path in (self._ssl_cert_crt, self._ssl_cert_key):
                    _utl.makedirs(_os_path.dirname(path), exist_ok=True)

        # Set HTTP/HTTPS as default depending on certificate
        if self._ssl_cert_crt:
            self._url = _utl.format_url(self._url, force_secure=True)

    def _get_role_and_policy(self, role, policy):
        """Get role and policy values from arguments and configuration file.

        Only for CSP supporting theses values.

        Args:
            role (str): Role argument value.
            policy (str): Policy argument value.

        Returns:
            tuple of str: role and policy
        """
        role = (role or self._config[self._config_section]['role'] or
                self._default_parameter_value('Role'))
        policy = (policy or self._config[self._config_section]['policy'] or
                  self._default_parameter_value('Policy'))
        return role, policy

    def _check_host_id_arguments(self):
        """
        Checks if enough arguments to start or get an instance.

        Raises:
            apyfal.exceptions.HostConfigurationException: Not enough arguments.
        """
        if (self._client_id is None and
                self._instance_id is None and self._url is None):
            raise _exc.HostConfigurationException(
                "Need at least 'client_id', 'instance_id' or 'host_ip' "
                "argument. See documentation for more information.")
