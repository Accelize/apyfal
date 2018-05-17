# coding=utf-8
"""Accelize AcceleratorAPI


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
__version__ = "2.1.0"
__copyright__ = "Copyright 2018 Accelize"
__licence__ = "Apache 2.0"

import acceleratorAPI.csp as _csp
import acceleratorAPI.accelerator as _acc
import acceleratorAPI.configuration as _cfg
import acceleratorAPI.exceptions as _exc
from acceleratorAPI._utilities import get_logger as _get_logger


class AcceleratorClass(object):
    """
    This class automatically handle AcceleratorClient and CSP classes.

    Args:
        accelerator_name (str): Name of the accelerator you want to initialize,
            to know the authorized list please visit "https://accelstore.accelize.com".
        config_file (str or acceleratorAPI.configuration.Configuration):
            Configuration file path or instance. If not set, will search it in current working directory, in current
            user "home" folder. If none found, will use default configuration values.
        provider (str): Cloud service provider name.
            If set will override value from configuration file.
        region (str): CSP region. Check with your provider which region are using instances with FPGA.
            If set will override value from configuration file.
        xlz_client_id (str): Accelize Client ID.
            Client Id is part of the access key you can generate on "https:/accelstore.accelize.com/user/applications".
            If set will override value from configuration file.
        xlz_secret_id (str): Accelize Secret ID.
            Secret Id is part of the access key you can generate on "https:/accelstore.accelize.com/user/applications".
            If set will override value from configuration file.
        csp_client_id (str): CSP Client ID. See with your provider to generate this value.
            If set will override value from configuration file.
        csp_secret_id (str): CSP secret ID. See with your provider to generate this value.
            If set will override value from configuration file.
        ssh_key (str): SSH key to use with your CSP. If set will override value from configuration file.
        instance_id (str): CSP Instance ID to reuse. If set will override value from configuration file.
        instance_url (str): CSP Instance URL or IP address to reuse. If set will override value from configuration file.
        stop_mode (int): CSP stop mode. See
            "acceleratorAPI.csp.CSPGenericClass.stop_mode" property for more
            information and possible values.
        exit_instance_on_signal (bool): If True, exit CSP instances
            on OS exit signals. This may help to not have instance still running
            if Python interpreter is not exited properly. Note: this is provided for
            convenience and does not cover all exit case like process kill and
            may not work on all OS.
    """
    def __init__(self, accelerator_name, config_file=None, provider=None,
                 region=None, xlz_client_id=None, xlz_secret_id=None, csp_client_id=None,
                 csp_secret_id=None, ssh_key=None, instance_id=None, instance_url=None,
                 stop_mode=_csp.TERM, exit_instance_on_signal=False):

        # Initialize configuration
        config = _cfg.create_configuration(config_file)

        # Create CSP object
        self._csp = _csp.CSPGenericClass(
            provider=provider, config=config, client_id=csp_client_id, secret_id=csp_secret_id, region=region,
            ssh_key=ssh_key, instance_id=instance_id, instance_url=instance_url,
            stop_mode=stop_mode, exit_instance_on_signal=exit_instance_on_signal)

        # Create AcceleratorClient object
        self._accelerator = _acc.AcceleratorClient(
            accelerator_name, client_id=xlz_client_id, secret_id=xlz_secret_id, config=config)

        # Check CSP ID if provided
        if instance_id:
            self._csp.instance_status()
            self._accelerator.url = self._csp.instance_url

        # Set CSP URL if provided
        elif instance_url:
            self._accelerator.url = instance_url

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.stop()

    def __del__(self):
        self.stop()

    @property
    def accelerator(self):
        """
        Accelerator instance.

        Returns:
            acceleratorAPI.accelerator.AcceleratorClient: Accelerator
        """
        return self._accelerator

    @property
    def csp(self):
        """
        Cloud Service Provider instance.

        Returns:
            acceleratorAPI.csp.CSPGenericClass subclass: Instance
        """
        return self._csp

    @property
    def instance_id(self):
        """
        ID of the current instance.

        Returns:
            str: ID

        Raises:
            acceleratorAPI.exceptions.CSPInstanceException:
                No instance from which get IP.
        """
        if self._csp is None:
            raise _exc.CSPInstanceException("No instance found")
        return self._csp.instance_id

    @property
    def instance_ip(self):
        """
        Public IP of the current instance.

        Returns:
            str: IP address

        Raises:
            acceleratorAPI.exceptions.CSPInstanceException:
                No instance from which get IP."""
        if self._csp is None:
            raise _exc.CSPInstanceException("No instance found")
        return self._csp.instance_ip

    def start(self, stop_mode=None, datafile=None, accelerator_parameters=None, **kwargs):
        """
        Starts and configure an accelerator instance.

        Args:
            stop_mode (int): CSP stop mode. If not None, override current "stop_mode" value.
                See "acceleratorAPI.csp.CSPGenericClass.stop_mode" property for more
                information and possible values.
            datafile (str): Depending on the accelerator (like for HyperFiRe),
                a configuration need to be loaded before a process can be run.
                In such case please define the path of the configuration file
                (for HyperFiRe the corpus file path).
            accelerator_parameters (dict): If set will overwrite the value content in the configuration file
                Parameters can be forwarded to the accelerator for the configuration step using these parameters.
                Take a look accelerator documentation for more information.
            kwargs:

        Returns:
            dict: AcceleratorClient response. Contain output information from configuration operation.
                Take a look accelerator documentation for more information.
        """
        # Start a new instance or use a running instance
        self._start_instance(stop_mode)

        # Configure accelerator if needed
        if kwargs or self._accelerator.configuration_url is None or datafile is not None:
            return self.configure(datafile, accelerator_parameters, **kwargs)

    def configure(self, datafile=None, accelerator_parameters=None, **kwargs):
        """
        Configure an accelerator instance.

        Args:
            datafile (str): Depending on the accelerator (like for HyperFiRe),
                a configuration need to be loaded before a process can be run.
                In such case please define the path of the configuration file
                (for HyperFiRe the corpus file path).
            accelerator_parameters (dict): If set will overwrite the value content in the configuration file
                Parameters can be forwarded to the accelerator for the configuration step using these parameters.
                Take a look accelerator documentation for more information.
            kwargs:

        Returns:
            dict: AcceleratorClient response. Contain output information from configuration operation.
                Take a look accelerator documentation for more information.
        """
        self._accelerator.is_alive()

        csp_env = self._csp.get_configuration_env(**kwargs)
        config_result = self._accelerator.start(
            datafile=datafile, accelerator_parameters=accelerator_parameters, csp_env=csp_env)

        return config_result

    def process(self, file_out, file_in=None, process_parameter=None):
        """
        Process a file with accelerator.

        Args:
            file_out (str): Path to the file you want to process.
            file_in (str): Path where you want the processed file will be stored.
            process_parameter (dict): If set will overwrite the value content in the configuration file Parameters
                an be forwarded to the accelerator for the process step using these parameters.
                Take a look accelerator documentation for more information.

        Returns:
            dict: AcceleratorClient response. Contain output information from process operation.
                Take a look accelerator documentation for more information.
        """
        # Process file with accelerator
        process_result = self._accelerator.process(
            file_in=file_in, file_out=file_out, accelerator_parameters=process_parameter)

        self._log_profiling_info(process_result)
        return process_result

    def stop(self, stop_mode=None):
        """
        Stop your accelerator session and accelerator csp instance depending of the parameters

        Args:
            stop_mode (int): CSP stop mode. If not None, override current "stop_mode" value.
                See "acceleratorAPI.csp.CSPGenericClass.stop_mode" property for more
                information and possible values.

        Returns:
            dict: AcceleratorClient response. Contain output information from stop operation.
                Take a look accelerator documentation for more information.
        """
        # Stops accelerator
        try:
            stop_result = self._accelerator.stop()

        # Stops CSP instance
        finally:
            self._csp.stop_instance(stop_mode)

        return stop_result

    def _start_instance(self, stop_mode=None):
        """
        Start a new instance or use a running instance.

        Args:
            stop_mode (int): CSP stop mode. If not None, override current "stop_mode" value.
                See "acceleratorAPI.csp.CSPGenericClass.stop_mode" property for more
                information and possible values.
        """
        # Get configuration information from webservice
        accel_requirements = self._accelerator.get_requirements(self._csp.provider)
        self._csp.set_accelerator_requirements(accel_requirements)

        # Start CSP instance if needed
        self._csp.start_instance()

        # Updates CSP Instance stop mode
        self._csp.stop_mode = stop_mode

        # Set accelerator URL to CSP instance URL
        self._accelerator.url = self._csp.instance_url

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
            logger.info("Profiling information from result:\n%s",
                        json.dumps(profiling, indent=4).replace('\\n', '\n').replace('\\t', '\t'))

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

            if total_bytes > 0.0 and global_time > 0.0:
                bw = total_bytes / global_time / 1024.0 / 1024.0
                fps = 1.0 / global_time
                logger.info(
                    "Server processing bandwidths on %s: round-trip = %0.1f MB/s, frame rate = %0.1f fps",
                    self._csp.provider, bw, fps)

            if total_bytes > 0.0 and fpga_time > 0.0:
                bw = total_bytes / fpga_time / 1024.0 / 1024.0
                fps = 1.0 / fpga_time
                logger.info(
                    "FPGA processing bandwidths on %s: round-trip = %0.1f MB/s, frame rate = %0.1f fps",
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
