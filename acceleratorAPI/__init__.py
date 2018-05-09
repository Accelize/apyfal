# coding=utf-8
"""Accelize AcceleratorAPI"""

__version__ = "2.0.3"

import json
import os
from acceleratorAPI import _utilities as _utl

# Initialize logger
logger = _utl.init_logger("acceleratorAPI", __file__)

# Not imported on top since need logger
import acceleratorAPI.csp as _csp
import acceleratorAPI.accelerator as _acc
import acceleratorAPI.configuration as _cfg


class AcceleratorClass(object):
    """
    This class automatically handle Accelerator and CSP classes.

    Args:
        accelerator_name:
        config_file:
        provider:
        region:
        xlz_client_id:
        xlz_secret_id:
        csp_client_id:
        csp_secret_id:
        ssh_key:
        instance_id:
        instance_url (str): CSP Instance URL or IP address
        stop_mode (int): CSP Stop Mode.
        exit_instance_on_signal (bool): If True, exit CSP instances
            on OS exit signals. This may help to not have instance still running
            if accelerator is not exited properly. Note: this is provided for
            convenience and does not cover all exit case like process kill and
            may not work on every OS.
    """
    def __init__(self, accelerator_name, config_file=None, provider=None,
                 region=None, xlz_client_id=None, xlz_secret_id=None, csp_client_id=None,
                 csp_secret_id=None, ssh_key=None, instance_id=None, instance_url=None,
                 stop_mode=_csp.TERM, exit_instance_on_signal=True):
        logger.debug("")
        logger.debug("/" * 100)

        # Initialize configuration
        config = _cfg.create_configuration(config_file)
        logger.info("Using configuration file: %s", config.file_path)

        # Create CSP object
        self._csp = _csp.CSPGenericClass(
            provider=provider, config=config, client_id=csp_client_id, secret_id=csp_secret_id, region=region,
            ssh_key=ssh_key, instance_id=instance_id, instance_url=instance_url,
            stop_mode=stop_mode, exit_instance_on_signal=exit_instance_on_signal)

        # Create Accelerator object
        self._accelerator = _acc.Accelerator(
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
            acceleratorAPI.accelerator.Accelerator: Accelerator
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

    def start(self, stop_mode=None, datafile=None, accelerator_parameters=None, **kwargs):
        # Start a new instance or use a running instance
        self._start_instance(stop_mode)

        # Configure accelerator if needed
        if kwargs or self._accelerator.configuration_url is None or datafile is not None:
            return self.configure(datafile, accelerator_parameters, **kwargs)
        logger.debug("Accelerator is already configured")

    def configure(self, datafile=None, accelerator_parameters=None, **kwargs):
        logger.debug("Configuring accelerator '%s' on instance ID %s", self._accelerator.name, self._csp.instance_id)
        self._accelerator.is_alive()

        csp_env = self._csp.get_configuration_env(**kwargs)
        config_result = self._accelerator.start_accelerator(
            datafile=datafile, accelerator_parameters=accelerator_parameters, csp_env=csp_env)

        logger.info("Configuration of accelerator is complete")
        return config_result

    def process(self, file_out, file_in=None, process_parameter=None):
        logger.debug("Starting a processing job: in=%s, out=%s", file_in, file_out)

        # Process file with accelerator
        process_result = self._accelerator.process_file(
            file_in=file_in, file_out=file_out, accelerator_parameters=process_parameter)

        self._log_profiling_info(process_result)
        return process_result

    def stop(self, stop_mode=None):
        # Stops accelerator
        stop_result = self._accelerator.stop_accelerator()

        # Stops CSP instance
        self._csp.stop_instance(stop_mode)

        return stop_result

    def _start_instance(self, stop_mode=None):
        """
        Start a new instance or use a running instance

        Args:
            stop_mode:
        """
        logger.debug("Starting instance on '%s'", self._csp.provider)

        # Get configuration information from webservice
        accel_requirements = self._accelerator.get_accelerator_requirements(self._csp.provider)
        self._csp.set_accelerator_requirements(accel_requirements)

        # Start CSP instance if needed
        self._csp.start_instance()

        # Updates CSP Instance stop mode
        self._csp.stop_mode = stop_mode

        # Set accelerator URL to CSP instance URL
        self._accelerator.url = self._csp.instance_url
        logger.info("Accelerator URL: %s", self._accelerator.url)

        # If possible use the last accelerator configuration (it can still be overwritten later)
        self._accelerator.use_last_configuration()

    def _log_profiling_info(self, process_result):
        """
        Shows profiling and specific information in logger.

        Args:
            process_result (dict): result from Accelerator.process_file
        """
        # Skips method if logger not at least on INFO Level
        if not logger.isEnabledFor(20):
            return None

        try:
            app = process_result['app']
        except KeyError:
            logger.debug("No application information found in result JSON file")
            return None

        # Handle profiling info
        try:
            profiling = app['profiling']
        except KeyError:
            logger.debug("No profiling information found in result JSON file")
        else:
            logger.info("Profiling information from result:\n%s",
                        json.dumps(profiling, indent=4).replace('\\n', '\n').replace('\\t', '\t'))

            # Compute and show information only on DEBUG level
            if logger.isEnabledFor(10):
                values = dict()

                for key in ('wall-clock-time', 'fpga-elapsed-time', 'total-bytes-written', 'total-bytes-read'):
                    try:
                        values[key] = float(profiling[key])
                    except KeyError:
                        logger.debug("No '%s' found in output JSON file." % key)

                total_bytes = values.get('total-bytes-written', 0.0) + values.get('total-bytes-read', 0.0)
                global_time = values.get('wall-clock-time', 0.0)
                fpga_time = values.get('fpga-elapsed-time', 0.0)

                if total_bytes > 0.0 and global_time > 0.0:
                    bw = total_bytes / global_time / 1024.0 / 1024.0
                    fps = 1.0 / global_time
                    logger.debug(
                        "Server processing bandwidths on %s: round-trip = %0.1f MB/s, frame rate = %0.1f fps",
                        self._csp.provider, bw, fps)

                if total_bytes > 0.0 and fpga_time > 0.0:
                    bw = total_bytes / fpga_time / 1024.0 / 1024.0
                    fps = 1.0 / fpga_time
                    logger.debug(
                        "FPGA processing bandwidths on %s: round-trip = %0.1f MB/s, frame rate = %0.1f fps",
                        self._csp.provider, bw, fps)

        # Handle Specific result
        try:
            specific = app['specific']
        except KeyError:
            logger.debug("No specific information found in result JSON file")
        else:
            if specific:
                logger.info("Specific information from result:\n%s",
                            json.dumps(specific, indent=4).replace('\\n', '\n')
                            .replace('\\t', '\t'))
