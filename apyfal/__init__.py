# coding=utf-8
"""Apyfal


Copyright 2018 Accelize

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
from __future__ import absolute_import

__version__ = "2.1.0"
__copyright__ = "Copyright 2018 Accelize"
__licence__ = "Apache 2.0"

import apyfal.csp as csp
import apyfal.client as _clt
import apyfal.exceptions as _exc
import apyfal.configuration as _cfg
from apyfal._utilities import get_logger as _get_logger


# Makes get_logger available here for easy access
get_logger = _get_logger


class Accelerator(object):
    """
    This class provides the full accelerator features by handling
    both Accelerator client and CSP.

    Args:
        accelerator (str): Name of the accelerator you want to initialize,
            to know the accelerator list please visit "https://accelstore.accelize.com".
        config (str or apyfal.configuration.Configuration): Configuration file path or instance.
            If not set, will search it in current working directory, in current
            user "home" folder. If none found, will use default configuration values.
        accelize_client_id (str): Accelize Client ID.
            Client ID is part of the access key you can generate on
            "https:/accelstore.accelize.com/user/applications".
        accelize_secret_id (str): Accelize Secret ID. Secret ID come with xlz_client_id.
        provider (str): Cloud service provider name.
        region (str): CSP region. Needs a region supporting instances with FPGA devices.
        client_id (str): CSP Access Key ID.
        secret_id (str): CSP Secret Access Key.
        instance_id (str): Instance ID of an already existing CSP instance to use.
            If not specified, create a new instance.
        instance_ip (str): IP address of an already existing CSP instance to use.
            If not specified, create a new instance..
        stop_mode (str or int): CSP stop mode.
            Default to 'term' if new instance, or 'keep' if already existing instance.
            See "apyfal.csp.CSPGeneric.stop_mode" property for more
            information and possible values.
        csp_kwargs: Keyword arguments related to specific CSP. See targeted CSP class
            to see full list of arguments.
    """
    def __init__(self, accelerator, config=None, accelize_client_id=None, accelize_secret_id=None,
                 provider=None, region=None, client_id=None, secret_id=None, instance_id=None,
                 instance_ip=None, stop_mode='term', **csp_kwargs):

        # Initialize configuration
        config = _cfg.create_configuration(config)

        # Create CSP object
        self._csp = csp.CSPGeneric(
            provider=provider, config=config, client_id=client_id, secret_id=secret_id,
            region=region, instance_id=instance_id, instance_ip=instance_ip,
            stop_mode=stop_mode, **csp_kwargs)

        # Create AcceleratorClient object
        self._client = _clt.AcceleratorClient(
            accelerator, accelize_client_id=accelize_client_id,
            accelize_secret_id=accelize_secret_id, config=config)

        # Try to pass CSP URL to Accelerator client if available
        try:
            self._client.url = self._csp.url
        except _exc.CSPException:
            pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.stop()

    def __del__(self):
        self.stop()

    @property
    def client(self):
        """
        Accelerator client.

        Returns:
            apyfal.client.AcceleratorClient: Accelerator client
        """
        return self._client

    @property
    def csp(self):
        """
        Accelerator CSP.

        Returns:
            apyfal.csp.CSPGeneric subclass: CSP Instance
        """
        return self._csp

    def start(self, stop_mode=None, datafile=None, info_dict=False, csp_env=None, **parameters):
        """
        Starts and/or configure an accelerator instance.

        Args:
            stop_mode (str or int): CSP stop mode. If not None, override current "stop_mode" value.
                See "apyfal.csp.CSPGeneric.stop_mode" property for more
                information and possible values.
            datafile (str): Depending on the accelerator (like for HyperFiRe),
                a configuration need to be loaded before a process can be run.
                In such case please define the path of the configuration file
                (for HyperFiRe the corpus file path).
            info_dict (bool): If True, returns a dict containing information on
                configuration operation.
            parameters (str or dict): Accelerator configuration specific parameters
                Can also be a full configuration parameters dictionary
                (Or JSON equivalent as str literal or path to file)
                Parameters dictionary override default configuration values,
                individuals specific parameters overrides parameters dictionary values.
                Take a look accelerator documentation for more information on possible parameters.

        Returns:
            dict: Optional, only if "info_dict" is True. AcceleratorClient response.
                  AcceleratorClient contain output information from  configuration operation.
                  Take a look to accelerator documentation for more information.
        """
        # Start CSP instance if needed (Do nothing if already started)
        self._csp.start(accel_client=self._client, stop_mode=stop_mode)

        # Set accelerator URL to CSP instance URL
        self._client.url = self._csp.url

        # Configure accelerator if needed
        return self._client.start(
            datafile=datafile,
            csp_env=self._csp.get_configuration_env(**(csp_env or dict())),
            info_dict=info_dict, **parameters)

    def process(self, file_in=None, file_out=None, info_dict=False, **parameters):
        """
        Process a file with accelerator.

        Args:
            file_in (str): Path where you want the processed file will be stored.
            file_out (str): Path to the file you want to process.
            info_dict (bool): If True, returns a dict containing information on
                process operation.
            parameters (str or dict): Accelerator process specific parameters
                Can also be a full process parameters dictionary
                (Or JSON equivalent as str literal or path to file)
                Parameters dictionary override default configuration values,
                individuals specific parameters overrides parameters dictionary values.
                Take a look accelerator documentation for more information on possible parameters.

        Returns:
            dict: Result from process operation, depending used accelerator.
            dict: Optional, only if "info_dict" is True. AcceleratorClient response.
                AcceleratorClient contain output information from  process operation.
                Take a look to accelerator documentation for more information.
        """
        info_dict = True if _get_logger().isEnabledFor(20) else info_dict

        # Process file with accelerator
        process_result = self._client.process(
            file_in=file_in, file_out=file_out, info_dict=info_dict, **parameters)

        self._log_profiling_info(process_result)
        return process_result

    def stop(self, stop_mode=None, info_dict=False):
        """
        Stop your accelerator session and accelerator csp instance depending of the parameters

        Args:
            stop_mode (str or int): CSP stop mode. If not None, override current "stop_mode" value.
                See "apyfal.csp.CSPGeneric.stop_mode" property for more
                information and possible values.
            info_dict (bool): If True, returns a dict containing information on
                stop operation.

        Returns:
            dict: Optional, only if "info_dict" is True. AcceleratorClient response.
                AcceleratorClient contain output information from  stop operation.
                Take a look to accelerator documentation for more information.
        """
        # Stops accelerator
        try:
            stop_result = self._client.stop(info_dict=info_dict)

        # Stops CSP instance
        finally:
            self._csp.stop(stop_mode)

        return stop_result

    def _log_profiling_info(self, process_result):
        """
        Shows profiling and specific information in logger.

        Args:
            process_result (dict): result from AcceleratorClient.process
        """
        logger = _get_logger()

        # Skips method if logger not at least on INFO Level
        if not logger.isEnabledFor(20):
            return None

        try:
            app = process_result['app']
        except KeyError:
            return None

        # Lazy import since not always called
        import json

        # Handle profiling info
        try:
            profiling = app['profiling']
        except KeyError:
            pass
        else:
            logger.info("Profiling information from result:")

            # Compute and show information only on DEBUG level
            values = dict()

            for key in ('wall-clock-time', 'fpga-elapsed-time', 'total-bytes-written', 'total-bytes-read'):
                try:
                    values[key] = float(profiling[key])
                except KeyError:
                    pass

            total_bytes = values.get('total-bytes-written', 0.0) + values.get('total-bytes-read', 0.0)
            global_time = values.get('wall-clock-time', 0.0)
            fpga_time = values.get('fpga-elapsed-time', 0.0)

            if global_time > 0.0:
                logger.info('- Total processing time: %.3fs' % global_time)

            if total_bytes > 0.0 and global_time > 0.0:
                bw = total_bytes / global_time / 1024.0 / 1024.0
                fps = 1.0 / global_time
                logger.info(
                    "- Server processing bandwidths on %s: round-trip = %0.1f MB/s, frame rate = %0.1f fps",
                    self._csp.provider, bw, fps)

            if total_bytes > 0.0 and fpga_time > 0.0:
                bw = total_bytes / fpga_time / 1024.0 / 1024.0
                fps = 1.0 / fpga_time
                logger.info(
                    "- FPGA processing bandwidths on %s: round-trip = %0.1f MB/s, frame rate = %0.1f fps",
                    self._csp.provider, bw, fps)

        # Handle Specific result
        try:
            specific = app['specific']
        except KeyError:
            pass
        else:
            if specific:
                logger.info("Specific information from result:\n%s",
                            json.dumps(specific, indent=4).replace('\\n', '\n')
                            .replace('\\t', '\t'))
