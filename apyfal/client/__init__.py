# coding=utf-8
"""Accelerator Client"""
from abc import abstractmethod as _abstractmethod
from contextlib import contextmanager as _contextmanager
from copy import deepcopy as _deepcopy
import json as _json
from os import remove as _remove
import os.path as _os_path
from shutil import rmtree as _rmtree
from tempfile import mkdtemp as _mkdtemp
from uuid import uuid4 as _uuid

import apyfal._utilities as _utl
import apyfal.exceptions as _exc
import apyfal.configuration as _cfg
import apyfal.storage as _srg
from apyfal._utilities import get_logger as _get_logger


class AcceleratorClient(_utl.ABC):
    """
    REST accelerator client.

    Args:
        accelerator (str): Name of the accelerator to initialize.
        client_type (str): Type of client.
        accelize_client_id (str): Accelize Client ID.
        accelize_secret_id (str): Accelize Secret ID.
        config (apyfal.configuration.Configuration, path-like object or file-like object):
            If not set, will search it in current working directory,
            in current user "home" folder. If none found, will use default
            configuration values.
            Path-like object can be path, URL or cloud object URL.
    """

    #: Client type name (str), must be the same as expected "client_type"
    # argument value
    NAME = None

    #: Default parameters JSON for configuration/start stage
    DEFAULT_CONFIGURATION_PARAMETERS = {
        "app": {"reset": False, "reload": True, "enable-sw-comparison": 0,
                "logging": {"format": 1, "verbosity": 2}, "specific": {}},
        "env": {}}

    #: Default parameters JSON for process stage
    DEFAULT_PROCESS_PARAMETERS = {
        "app": {"reset": False, "enable-sw-comparison": 0,
                "logging": {"format": 1, "verbosity": 4}, "specific": {}}}

    # Client is remote or not
    REMOTE = False

    # Format required for parameter: 'file' or 'stream' (default)
    _PARAMETER_IO_FORMAT = {}

    #: Default directories that can be processed remotely on host
    DEFAULT_AUTHORIZED_HOST_DIRS = ['~/shared']

    def __new__(cls, *args, **kwargs):
        # If call from a subclass, instantiate this subclass directly
        if cls is not AcceleratorClient:
            return object.__new__(cls)

        # Get client_type from configuration or argument
        client_type = kwargs.get('client_type') or 'SysCall'

        # Get client subclass
        return _utl.factory(
            cls, client_type, 'client_type', _exc.ClientConfigurationException)

    def __init__(self, accelerator=None, client_type=None,
                 accelize_client_id=None, accelize_secret_id=None, config=None,
                 **_):
        self._name = accelerator
        self._client_type = client_type
        self._url = None
        self._stopped = False

        # Define a session UUID
        self._session_uuid = str(_uuid())

        # Dict to cache values
        self._cache = {}

        # Read configuration
        self._config = config = _cfg.create_configuration(config)

        # Get Start parameters
        self._configuration_parameters = self._load_configuration(
            self.DEFAULT_CONFIGURATION_PARAMETERS, 'configuration')

        # Add credential information if available
        client_id = config['accelize'].set('client_id', accelize_client_id)
        if client_id:
            self._configuration_parameters['env']['client_id'] = client_id
        secret_id = config['accelize'].set('secret_id', accelize_secret_id)
        if secret_id:
            self._configuration_parameters['env']['client_secret'] = secret_id

        #: Directories that can be processed remotely on host
        self._authorized_host_dirs = [
            '%s/' % _os_path.abspath(_os_path.expanduser(path)) for path in (
                config['security'].get_list('authorized_host_dirs') or
                self.DEFAULT_AUTHORIZED_HOST_DIRS)]

        # Get process parameters
        self._process_parameters = self._load_configuration(
            self.DEFAULT_PROCESS_PARAMETERS, 'process')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.__del__()

    def __del__(self):
        if self._stopped:
            # Avoid double call with __exit__ + __del__
            return
        self.stop(full_stop=False)

    def __str__(self):
        return "<%s.%s accelerator='%s' type='%s'%s>" % (
            self.__class__.__module__, self.__class__.__name__, self._name,
            self._client_type, " url='%s'" % self._url if self._url else '')

    __repr__ = __str__

    @property
    def name(self):
        """
        Accelerator name

        Returns:
            str: name
        """
        return self._name

    def start(self, src=None, info_dict=None, host_env=None, reload=None,
              reset=None, **parameters):
        """
        Configures accelerator.

        Args:
            src (path-like object or file-like object): Depending on the
                accelerator, a configuration data need to be loaded before
                a process can be run.
                Path-like object can be path, URL or cloud object URL.
            parameters (str, path-like object or dict):
                Accelerator configuration specific
                parameters Can also be a full configuration parameters
                dictionary (Or JSON equivalent as str literal or apyfal.storage
                URL to file) Parameters dictionary override default
                configuration values, individuals specific parameters overrides
                parameters dictionary values. Take a look to accelerator
                documentation for more information on possible parameters.
                Path-like object can be path, URL or cloud object URL.
            reload (bool): Force reload of FPGA bitstream.
            reset (bool): Force reset of FPGA logic.
            info_dict (dict or None): If a dict passed, this dict is updated
                with extra information from current operation.
            host_env (dict): Overrides Accelerator "env".
        """
        self._stopped = False

        _get_logger().info("Configuring accelerator...")

        # Configure start
        parameters = self._get_parameters(
            parameters, self._configuration_parameters)
        parameters['env'].update(host_env or dict())

        # Set FPGA reset and reload options
        if reload is not None:
            parameters['app']['reload'] = reload
        if reset is not None:
            parameters['app']['reset'] = reset

        # Handle files
        with self._data_file(
                src, parameters, ('src', 'datafile'), mode='rb') as src:
            # Starts
            response = self._start(src, parameters)

        # Check response status
        self._raise_for_status(response, "Failed to configure accelerator: ")

        _get_logger().info("Accelerator ready")

        # Update info dict
        if info_dict is not None and response:
            _utl.recursive_update(info_dict, response)

    @_abstractmethod
    def _start(self, src, parameters):
        """
        Client specific start implementation.

        Args:
            src (str or file-like object): Input data.
            parameters (dict): Parameters dict.

        Returns:
            dict: response.
        """

    def process(self, src=None, dst=None, info_dict=None,
                **parameters):
        """
        Processes with accelerator.

        Args:
            src (path-like object or file-like object):
                Source data to process.
                Path-like object can be path, URL or cloud object URL.
            dst (path-like object or file-like object):
                Processed data destination.
                Path-like object can be path, URL or cloud object URL.
            parameters (path-like object, str or dict): Accelerator process
                specific parameters
                Can also be a full process parameters dictionary
                (Or JSON equivalent as str literal) Parameters dictionary
                override default configuration
                values, individuals specific parameters overrides parameters
                dictionary values. Take a look to accelerator documentation for
                more information on possible parameters.
                Path-like object can be path, URL or cloud object URL.
            info_dict (dict or None): If a dict passed, this dict is updated
                with extra information from current operation.

        Returns:
            Result from process operation, depending used accelerator.
        """
        # Configures processing
        parameters = self._get_parameters(parameters, self._process_parameters)

        # Handle files
        with self._data_file(
                src, parameters, ('src', 'file_in'), mode='rb') as src:
            with self._data_file(
                    dst, parameters, ('dst', 'file_out'), mode='wb') as dst:
                # Processes
                response = self._process(src, dst, parameters)

        # Check response status
        self._raise_for_status(response, "Processing failed: ")

        # Get result from response
        result = response['app'].pop('specific', None)

        # Update info dict
        if info_dict is not None and response:
            _utl.recursive_update(info_dict, response)

        # Returns result
        return result

    @_abstractmethod
    def _process(self, src, dst, parameters):
        """
        Client specific process implementation.

        Args:
            src (str or file-like object): Input data.
            dst (str or file-like object): Output data.
            parameters (dict): Parameters dict.

        Returns:
            dict: response.
        """

    def stop(self, info_dict=None, full_stop=True):
        """
        Stop accelerator.

        Args:
            full_stop (bool): If True, send stop request to accelerator
                application. If False only clean up accelerator client
                environment.
            info_dict (dict or None): If a dict passed, this dict is updated
                with extra information from current operation.
        """
        self._stopped = True

        # Stops
        if full_stop:
            response = self._stop()
            if info_dict is not None and response:
                _utl.recursive_update(info_dict, response)

        # Clears temporary directory
        try:
            _rmtree(self._cache['tmp_dir'])
        except (OSError, KeyError):
            pass

        # Clears cache
        self._cache.clear()

    @_abstractmethod
    def _stop(self):
        """
        Client specific stop implementation.

        Returns:
            dict or None: response.
        """

    @staticmethod
    def _raise_for_status(api_result, message=""):
        """
        Check accelerator results and raise exception in case of error.

        Args:
            api_result (dict): Result from accelerator.
            message (str): Optional exception message to add before accelerator
                message.

        Raises:
            apyfal.exceptions.ClientRuntimeException: Exception from arguments.
        """
        try:
            status = api_result['app']['status']
        except KeyError:
            raise _exc.ClientRuntimeException('%sNo result returned' % message)
        if status:
            raise _exc.ClientRuntimeException(
                message + api_result['app']['msg'])

    @staticmethod
    def _get_parameters(parameters, default_parameters, copy=True):
        """
        Gets parameters from different sources, and merge them together.

        If 'parameters' contain a key named 'parameters', it will be
        read as a full parameter dict, or JSON literal or JSON file URL.

        Other keys from 'parameters' will be merged to the 'specific'
        section of the result dict.

        Args:
            parameters (dict): parameters
            default_parameters (dict): default parameters
            copy (bool): If True return a copy of updated default_parameters,
                else update directly.

        Returns:
            dict : parameters.
        """
        # Takes default parameters as basis
        if copy:
            result = _deepcopy(default_parameters)
        else:
            result = default_parameters

        # Gets parameters from included JSON file
        json_parameters = parameters.pop('parameters', None)
        if json_parameters:
            # Reads JSON parameter from file or literal
            if not isinstance(json_parameters, dict):
                # JSON literal
                if json_parameters.rstrip().startswith('{'):
                    json_parameters = _json.loads(json_parameters)

                # JSON file
                else:
                    with _srg.open(json_parameters, 'rt') as json_file:
                        json_parameters = _json.load(json_file)

            # Merges to result
            _utl.recursive_update(result, json_parameters)

        # Merges other parameters to specific section of parameters
        try:
            specific = result['app']['specific']
        except KeyError:
            specific = result['app']['specific'] = dict()
        _utl.recursive_update(specific, parameters)

        return result

    def _load_configuration(self, default_parameters, section):
        """Load parameters from configuration.

        Args:
            default_parameters (dict): default parameters
            section (str): Section in configuration."""
        # Load default parameters
        parameters = _deepcopy(default_parameters)

        # Update with configuration
        for section in (
                section, '%s.%s' % (section, self._name)):
            self._get_parameters(
                {key: self._config[section].get_literal(key)
                 for key in self._config[section]}, parameters, copy=False)
        return parameters

    @_contextmanager
    def _data_file(self, url, parameters, parameter_name, mode):
        """Get files with apyfal.storage.

        Args:
            url (str or file-like object): Input URL.
            parameters (dict): Parameters dict.
            parameter_name (str or tuple of str): Parameter name for input URL.
            mode (str): Access mode. 'r' or 'w'.

        Returns:
            str or file-like object or None:
                Local version of input path.
        """
        # Apyfal 1.1.0 Compatibility
        if isinstance(parameter_name, tuple):
            parameter_name, ap110_name = parameter_name
        else:
            ap110_name = parameter_name

        # No URL
        if url is None:
            # Get URL from parameters if not provided directly
            try:
                url = parameters['app']['specific'].pop(parameter_name)

            # Still no URL, yields directly
            except KeyError:

                # Apyfal 1.1.0 Compatibility
                url = parameters['app']['specific'].pop(ap110_name, None)
                if url is None:

                    yield None
                    return

        # Gets scheme and path from URL
        scheme, path = _srg.parse_url(url, not self.REMOTE)

        # File scheme: Check paths
        if scheme == 'file':
            path = _os_path.abspath(path)

            # Only authorises files in whitelisted directories on host
            if not self.REMOTE and url.startswith('host://'):
                for authorized in self._authorized_host_dirs:
                    if not path.startswith(authorized):
                        raise _exc.ClientSecurityException(
                            "Unauthorized path: '%s'" % path)

            # Checks input file exists
            if 'r' in mode and not _os_path.isfile(path):
                raise _exc.ClientConfigurationException(
                    gen_msg=('not_found_named', parameter_name, path))

            # Ensures output parent directory exists
            elif 'w' in mode:
                _utl.makedirs(_os_path.dirname(path), exist_ok=True)

        # Client side:
        # Sends URL to host side as parameters and
        # yields None to client
        if self.REMOTE and scheme not in ('stream', 'file'):
            parameters['app']['specific'][parameter_name] = url

            # Apyfal 1.1.0 Compatibility
            if ap110_name != parameter_name:
                parameters['app']['specific'][ap110_name] = url

            yield None

        # Other case, yields file in expected format (file or stream)
        else:
            # As file
            if self._PARAMETER_IO_FORMAT.get(
                    parameter_name, 'stream') == 'file':

                # Already a file
                if scheme == 'file':
                    yield path

                # Use temporary file
                else:
                    with self.as_tmp_file(url, mode) as file:
                        yield file
            # As stream
            else:
                with _srg.open(url, mode) as stream:
                    yield stream

    @_contextmanager
    def as_tmp_file(self, url, mode):
        """
        Return temporary representation of a file.

        Args:
            url (str): apyfal.storage URL of the file.
            mode (str): Access mode. 'r' or 'w'.

        Returns:
            str or file-like object: temporary object.
        """
        # Generates randomized temporary filename
        local_path = _os_path.join(
            self._tmp_dir, str(_uuid()))

        # Gets input file
        if 'r' in mode:
            _srg.copy(url, local_path)

        # Yields local temporary path
        yield local_path

        # Sends output file
        if 'w' in mode:
            _srg.copy(local_path, url)

        # Clears temporary file
        _remove(local_path)

    @property
    def _tmp_dir(self):
        """
        Current client temporary directory.

        Returns:
            str: Current temporary directory path.
        """
        try:
            return self._cache['tmp_dir']
        except KeyError:
            self._cache['tmp_dir'] = _mkdtemp(dir=_cfg.ACCELERATOR_TMP_ROOT)
            return self._cache['tmp_dir']
