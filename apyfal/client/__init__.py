"""Accelerator Client"""
from abc import abstractmethod as _abstractmethod
from copy import deepcopy as _deepcopy
import json as _json

import apyfal._utilities as _utl
import apyfal.exceptions as _exc
import apyfal.configuration as _cfg


class AcceleratorClient(_utl.ABC):
    """
    REST accelerator client.

    Args:
        accelerator (str): Name of the accelerator to initialize,
            to know the accelerator list please visit "https://accelstore.accelize.com".
        client_type (str): Type of client.
        accelize_client_id (str): Accelize Client ID.
            Client ID is part of the access key generate from
            "https:/accelstore.accelize.com/user/applications".
        accelize_secret_id (str): Accelize Secret ID. Secret ID come with client_id.
        config (str or apyfal.configuration.Configuration or file-like object):
            Can be Configuration instance, apyfal.storage URL, paths, file-like object.
            If not set, will search it in current working directory, in current
            user "home" folder. If none found, will use default configuration values.
    """

    #: Client type name (str), must be the same as expected "client_type" argument value
    NAME = None

    #: Default parameters JSON for configuration/start stage
    DEFAULT_CONFIGURATION_PARAMETERS = {
        "app": {
            "reset": 0,
            "enable-sw-comparison": 0,
            "logging": {"format": 1, "verbosity": 2},
            "specific": {}},
        "env": {}}

    #: Default parameters JSON for process stage
    DEFAULT_PROCESS_PARAMETERS = {
        "app": {
            "reset": 0,
            "enable-sw-comparison": 0,
            "logging": {"format": 1, "verbosity": 2},
            "specific": {}}}

    def __new__(cls, *args, **kwargs):
        # If call from a subclass, instantiate this subclass directly
        if cls is not AcceleratorClient:
            return object.__new__(cls)

        # Get client_type from configuration or argument
        client_type = kwargs.get('client_type') or 'SysCall'

        # Get client subclass
        return _utl.factory(
            cls, client_type, 'client_type', _exc.ClientConfigurationException)

    def __init__(self, accelerator, client_type=None, accelize_client_id=None,
                 accelize_secret_id=None, config=None, **_):
        self._name = accelerator
        self._client_type = client_type
        self._url = None
        self._stopped = False

        # Read configuration
        self._config = config = _cfg.create_configuration(config)

        self._configuration_parameters = self._load_configuration(
            self.DEFAULT_CONFIGURATION_PARAMETERS, 'configuration')
        self._configuration_parameters['env'].update({
            "client_id":
                config['accelize'].set('client_id', accelize_client_id),
            "client_secret":
                config['accelize'].set('secret_id', accelize_secret_id)})

        self._process_parameters = self._load_configuration(
            self.DEFAULT_PROCESS_PARAMETERS, 'process')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.stop()

    def __del__(self):
        self.stop()

    @property
    def name(self):
        """
        Accelerator name

        Returns:
            str: name
        """
        return self._name

    def start(self, datafile=None, info_dict=False, host_env=None, **parameters):
        """
        Configures accelerator.

        Args:
            datafile (str): Depending on the accelerator,
                a configuration need to be loaded before a process can be run.
                In such case please define the path of the configuration file.
            info_dict (bool): If True, returns a dict containing information on
                configuration operation.
            parameters (str or dict): Accelerator configuration specific parameters
                Can also be a full configuration parameters dictionary
                (Or JSON equivalent as str literal or path to file)
                Parameters dictionary override default configuration values,
                individuals specific parameters overrides parameters dictionary values.
                Take a look to accelerator documentation for more information on possible parameters.

        Returns:
            dict: Optional, only if "info_dict" is True. AcceleratorClient response.
                AcceleratorClient contain output information from  configuration operation.
                Take a look accelerator documentation for more information.
        """
        # Configure start
        parameters = self._get_parameters(parameters, self._configuration_parameters)
        parameters['env'].update(host_env or dict())

        # Starts
        response = self._start(datafile, info_dict, parameters)

        # Returns optional response
        if info_dict:
            return response

    @_abstractmethod
    def _start(self, datafile, info_dict, parameters):
        """
        Client specific start implementation.

        Args:
            datafile (str): Input file.
            info_dict (bool): Returns response dict.
            parameters (dict): Parameters dict.

        Returns:
            dict or None: response.
        """

    def process(self, file_in=None, file_out=None, info_dict=False, **parameters):
        """
        Processes with accelerator.

        Args:
            file_in (str): Path to the file to process.
            file_out (str): Path where the processed file will be stored.
            info_dict (bool): If True, returns a dict containing information on
                process operation.
            parameters (str or dict): Accelerator process specific parameters
                Can also be a full process parameters dictionary
                (Or JSON equivalent as str literal or path to file)
                Parameters dictionary override default configuration values,
                individuals specific parameters overrides parameters dictionary values.
                Take a look to accelerator documentation for more information on possible parameters.

        Returns:
            dict: Result from process operation, depending used accelerator.
            dict: Optional, only if "info_dict" is True. AcceleratorClient response.
                AcceleratorClient contain output information from  process operation.
                Take a look accelerator documentation for more information.
        """
        # Configures processing
        parameters = self._get_parameters(parameters, self._process_parameters)

        # Processes
        response = self._process(file_in, file_out, parameters)

        # Get result from response
        try:
            result = response['app'].pop('specific')
        except KeyError:
            result = dict()

        # Returns result
        if info_dict:
            # Returns it with optional response
            return result, response
        return result

    @_abstractmethod
    def _process(self, file_in, file_out, parameters):
        """
        Client specific process implementation.

        Args:
            file_in (str): Input file.
            file_out (str): Output file.
            parameters (dict): Parameters dict.

        Returns:
            dict: response.
        """

    def stop(self, info_dict=False):
        """
        Stop accelerator.

        Args:
            info_dict (bool): If True, returns a dict containing information on
                stop operation.

        Returns:
            dict: Optional, only if "info_dict" is True. AcceleratorClient response.
                AcceleratorClient contain output information from  stop operation.
                Take a look to accelerator documentation for more information.
        """
        # Stops
        response = self._stop(info_dict)

        # Returns optional response
        if info_dict:
            return response

    @_abstractmethod
    def _stop(self, info_dict):
        """
        Client specific stop implementation.

        Args:
            info_dict (bool): Returns response dict.

        Returns:
            dict or None: response.
        """

    @staticmethod
    def _raise_for_status(api_result, message=""):
        """
        Check accelerator results and raise exception in case of error.

        Args:
            api_result (dict): Result from accelerator.
            message (str): Optional exception message to add before accelerator message.

        Raises:
            apyfal.exceptions.ClientRuntimeException: Exception from arguments.
        """
        try:
            status = api_result['app']['status']
        except KeyError:
            raise _exc.ClientRuntimeException('%sNo result returned' % message)
        if status:
            raise _exc.ClientRuntimeException(message + api_result['app']['msg'])

    @staticmethod
    def _get_parameters(parameters, default_parameters):
        """
        Gets parameters from different sources, and merge them together.

        If 'parameters' contain a key named 'parameters', it will be
        read as a full parameter dict, or JSON literal or JSON file.

        Other keys from 'parameters' will be merged to the 'specific'
        section of the result dict.

        Args:
            parameters (dict): parameters
            default_parameters (dict): default parameters

        Returns:
            dict : parameters.
        """
        # Takes default parameters as basis
        result = _deepcopy(default_parameters)

        # Gets parameters from included JSON file
        try:
            json_parameters = parameters.pop('parameters')
        except KeyError:
            pass
        else:
            # Reads JSON parameter from file or literal
            if isinstance(json_parameters, str):
                # JSON literal
                if json_parameters.startswith('{'):
                    json_parameters = _json.loads(json_parameters)

                # JSON file
                else:
                    with open(json_parameters, 'rt') as json_file:
                        json_parameters = _json.load(json_file)

            # Merges to result
            result.update(json_parameters)

        # Merges other parameters to specific section of parameters
        try:
            specific = result['app']['specific']
        except KeyError:
            specific = result['app']['specific'] = dict()
        specific.update(parameters)

        return result

    def _load_configuration(self, default_parameters, section):
        """Load parameters from configuration.

        Args:
            default_parameters (dict): default parameters
            section (str): Section in configuration."""
        # Load default parameters
        parameters = _deepcopy(default_parameters)

        # Update with configuration
        config = self._config['%s.%s' % (section, self._name)]
        _utl.recursive_update(
            parameters, config.get_literal('parameters') or {})
        return parameters
