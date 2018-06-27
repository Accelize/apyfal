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
        accelize_client_id (str): Accelize Client ID.
            Client ID is part of the access key generate from
            "https:/accelstore.accelize.com/user/applications".
        accelize_secret_id (str): Accelize Secret ID. Secret ID come with client_id.
        host_ip (str): IP or URL address of the accelerator host.
        config (str or apyfal.configuration.Configuration or file-like object):
            Can be Configuration instance, apyfal.storage URL, paths, file-like object.
            If not set, will search it in current working directory, in current
            user "home" folder. If none found, will use default configuration values.
    """

    #: Default parameters JSON for configuration/start stage
    DEFAULT_CONFIGURATION_PARAMETERS = {"app": {
        "reset": 0,
        "enable-sw-comparison": 0,
        "logging": {"format": 1, "verbosity": 2},
        "specific": {}}}

    #: Default parameters JSON for process stage
    DEFAULT_PROCESS_PARAMETERS = {"app": {
        "reset": 0,
        "enable-sw-comparison": 0,
        "logging": {"format": 1, "verbosity": 2},
        "specific": {}}}

    def __new__(cls, *args, **kwargs):
        if cls is not AcceleratorClient:
            return object.__new__(cls)

        # TODO: Select Client subclass base on configuration
        from apyfal.client.rest import RESTClient
        return object.__new__(RESTClient)

    def __init__(self, accelerator, accelize_client_id=None,
                 accelize_secret_id=None, host_ip=None, config=None):
        self._name = accelerator
        self._url = None
        self._stopped = False

        # Read configuration
        self._config = config = _cfg.create_configuration(config)
        self._client_id = config['accelize'].set('client_id', accelize_client_id)
        self._secret_id = config['accelize'].set('secret_id', accelize_secret_id)

        self._configuration_parameters = self._load_configuration(
            self.DEFAULT_CONFIGURATION_PARAMETERS, 'configuration')
        self._process_parameters = self._load_configuration(
            self.DEFAULT_PROCESS_PARAMETERS, 'process')

        # Sets URL and configures
        if host_ip:
            self.url = host_ip

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

    @property
    def url(self):
        """
        URL of the accelerator host.

        Returns:
            str: URL
        """
        return self._url

    @url.setter
    def url(self, url):
        # Check URL
        if not url:
            raise _exc.ClientConfigurationException("Host URL is not valid.")

        self._url = _utl.format_url(url)

    @_abstractmethod
    def start(self, datafile=None, info_dict=False, host_env=None, **parameters):
        """
        Create an AcceleratorClient configuration.

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

    @_abstractmethod
    def process(self, file_in=None, file_out=None, info_dict=False, **parameters):
        """
        Process a file with accelerator.

        Args:
            file_in (str): Path to the file you want to process.
            file_out (str): Path where you want the processed file will be stored.
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

    @_abstractmethod
    def stop(self, info_dict=False):
        """
        Stop your accelerator session.

        Args:
            info_dict (bool): If True, returns a dict containing information on
                stop operation.

        Returns:
            dict: Optional, only if "info_dict" is True. AcceleratorClient response.
                AcceleratorClient contain output information from  stop operation.
                Take a look to accelerator documentation for more information.
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
