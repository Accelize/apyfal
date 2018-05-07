# coding=utf-8
"""Accelize AcceleratorAPI"""

__version__ = "2.0.3"

import json
import os
import socket
from acceleratorAPI import _utilities as _utl

# Initialize logger
logger = _utl.init_logger("acceleratorAPI", __file__)


# Create base exception class
class AcceleratorApiBaseException(Exception):
    """Base exception for acceleratorAPI exceptions"""


# Not imported on top since need AcceleratorApiBaseException
import acceleratorAPI.csp as _csp
import acceleratorAPI.accelerator as _acc
import acceleratorAPI.configuration as _cfg


TERM = 0
STOP = 1
KEEP = 2


class _SignalHandlerAccelerator(object):
    """
    Signal handler for instances

    Args:
        parent (AcceleratorClass): Parent instance.
    """
    _SOCKET_TIMEOUT = 1200  # seconds

    def __init__(self, parent):
        self._parent = parent
        self._set_signals()
        self._default_socket_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(self._SOCKET_TIMEOUT)

    @property
    def _stop_mode(self):
        return self._parent.stop_mode

    @property
    def _csp(self):
        return self._parent.csp_instance

    def _set_signals(self):
        """
        Set a list of interrupt signals to be handled asynchronously
        """
        # Lazy import since only used with AcceleratorClass
        import signal

        for signal_name in ('SIGTERM', 'SIGINT', 'SIGQUIT'):
            # Check signal exist on current OS before setting it
            if hasattr(signal, signal_name):
                signal.signal(getattr(signal, signal_name), self.signal_handler_accelerator)

    def signal_handler_accelerator(self, _signo="", _stack_frame="", exit_interpreter=True):
        """
        Try to stop all instances running or inform user.

        Args:
            _signo:
            _stack_frame:
            exit (bool):
        """
        try:
            if self._csp is None:
                logger.debug("There is no registered instance to stop")
                return
            if self._stop_mode == KEEP or not self._csp.is_instance_id_valid():
                logger.warning("###########################################################")
                logger.warning("## Instance with URL %s (ID=%s) is still running!",
                               self._csp.instance_url, self._csp.instance_id)
                logger.warning("## Make sure you will stop manually the instance.")
                logger.warning("###########################################################")
            else:
                terminate = True if self._stop_mode == TERM else False
                self._csp.stop_instance(terminate)
        finally:
            logger.info("More detailed messages can be found in %s", logger.filename)
            if exit_interpreter:
                socket.setdefaulttimeout(self._default_socket_timeout)
                logger.info("Accelerator API Closed properly")
                os._exit(0)


class AcceleratorClass(object):
    """
    This class automatically handle Accelerator and CSP classes.

    Args:
        accelerator:
        config_file:
        provider:
        region:
        xlz_client_id:
        xlz_secret_id:
        csp_client_id:
        csp_secret_id:
        ssh_key:
        instance_id:
        instance_ip:
        exit_instance_on_signal (bool): If True, exit CSP instances
            on OS exit signals. This may help to not have instance still running
            if accelerator is not exited properly. Note: this is provided for
            convenience and does not cover all exit case like process kill and
            may not work on every OS.
    """
    def __init__(self, accelerator_name, config_file=None, provider=None,
                 region=None, xlz_client_id=None, xlz_secret_id=None, csp_client_id=None,
                 csp_secret_id=None, ssh_key=None, instance_id=None, instance_ip=None,
                 exit_instance_on_signal=True):
        logger.debug("")
        logger.debug("/" * 100)

        # Initialize configuration
        config = _cfg.create_configuration(config_file)
        logger.info("Using configuration file: %s", config.file_path)

        # Create CSP object
        instance_url = ("http://%s" % instance_ip) if instance_ip else None
        self._csp = _csp.CSPGenericClass(
            provider=provider, config=config, client_id=csp_client_id, secret_id=csp_secret_id, region=region,
            ssh_key=ssh_key, instance_id=instance_id, instance_url=instance_url)

        # Handle CSP instance stop
        self._stop_mode = int(config.get_default("csp", "stop_mode", default=TERM))
        if exit_instance_on_signal:
            self._sign_handler = _SignalHandlerAccelerator(self)
        else:
            self._sign_handler = None

        # Create Accelerator object
        self._accelerator = _acc.Accelerator(
            accelerator_name, client_id=xlz_client_id, secret_id=xlz_secret_id, config=config)

        # Checking if credentials are valid otherwise no sense to continue
        self._accelerator.check_accelize_credential()

        # Check CSP ID if provided
        if instance_id:
            self._csp.get_instance_status()
            self._accelerator.url = self._csp.get_instance_url()

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
    def stop_mode(self):
        """
        Stop mode

        Returns:
            int: stop mode
        """
        return self._stop_mode

    @stop_mode.setter
    def stop_mode(self, stop_mode):
        if stop_mode is None:
            return

        try:
            stop_mode = int(stop_mode)
        except TypeError:
            pass

        stop_modes = {
            TERM: "TERM",
            STOP: "STOP",
            KEEP: "KEEP"}

        if stop_mode not in stop_modes:
            raise ValueError(
                "Invalid value %s, Possible values are %s" % (
                    stop_mode, ', '.join("%s: %d" % (name, value)
                                         for value, name in stop_modes.items())))

        self._stop_mode = stop_mode
        logger.info("Auto-stop mode is: %s", stop_modes[self._stop_mode])

    @property
    def csp_instance(self):
        """
        CSP instance

        Returns:
            acceleratorAPI.csp.CSPGenericClass subclass: Instance
        """
        return self._csp

    # Start a new instance or use a running instance
    def start_instance(self, stop_mode=None):
        logger.debug("Starting instance on '%s'", self._csp.provider)

        # Updates stop mode
        if stop_mode is not None:
            self.stop_mode = stop_mode

        # Get configuration information from webservice
        accel_requirements = self._accelerator.get_accelerator_requirements(self._csp.provider)
        self._csp.set_accelerator_requirements(accel_requirements)

        # Start CSP instance if needed
        if self._csp.instance_url is None:
            self._csp.check_credential()

            if self._csp.instance_id is None:
                self._csp.create_instance()

            self._csp.start_instance()
            self._accelerator.url = self._csp.get_instance_url()

        logger.info("Accelerator URL: %s", self._accelerator.url)

        # If possible use the last accelerator configuration (it can still be overwritten later)
        self._accelerator.use_last_configuration()

    def configure_accelerator(self, datafile=None, accelerator_parameters=None, **kwargs):
        logger.debug("Configuring accelerator '%s' on instance ID %s", self._accelerator.name, self._csp.instance_id)
        self._accelerator.is_alive()

        csp_env = self._csp.get_configuration_env(**kwargs)
        config_result = self._accelerator.start_accelerator(
            datafile=datafile, accelerator_parameters=accelerator_parameters, csp_env=csp_env)

        logger.info("Configuration of accelerator is complete")
        return config_result

    def start(self, stop_mode=None, datafile=None, accelerator_parameters=None, **kwargs):
        # Start a new instance or use a running instance
        self.start_instance(stop_mode)

        # Configure accelerator if needed
        if kwargs or self._accelerator.configuration_url is None or datafile is not None:
            return self.configure_accelerator(datafile, accelerator_parameters, **kwargs)
        logger.debug("Accelerator is already configured")

    def process(self, file_out, file_in=None, process_parameter=None):
        logger.debug("Starting a processing job: in=%s, out=%s", file_in, file_out)

        # Checks input file presence
        if file_in and not os.path.isfile(file_in):
            raise OSError("Could not find input file: %s", file_in)

        # Checks output directory presence, and creates it if not exists.
        if file_out:
            try:
                os.makedirs(os.path.dirname(file_out))
            except OSError:
                pass

        # Checks Accelerator URL
        logger.debug("Accelerator URL: %s", self._accelerator.url)
        self._accelerator.is_alive()

        # Process file with accelerator
        process_result = self._accelerator.process_file(
            file_in=file_in, file_out=file_out, accelerator_parameters=process_parameter)

        self._log_profiling_info(process_result)
        return process_result

    def stop_accelerator(self):
        logger.debug("Stopping accelerator '%s' on instance ID %s", self._accelerator.name, self._csp.instance_id)
        try:
            self._accelerator.is_alive()
        except _acc.AcceleratorRuntimeException:
            return

        stop_result = self._accelerator.stop_accelerator()
        logger.info("Accelerator session is closed")
        return stop_result

    def stop_instance(self, terminate=True):
        logger.debug("Stopping instance (ID: %s) on '%s'", self._csp.instance_id, self._csp.provider)

        stop_result = self.stop_accelerator()
        self._csp.stop_instance(terminate)

        return stop_result

    def stop(self, stop_mode=None):
        stop_mode = self.stop_mode if stop_mode is None else stop_mode

        # Stops accelerator only
        if stop_mode == KEEP:
            return self.stop_accelerator()

        # Stops accelerator + instance
        return self.stop_instance(True if stop_mode == TERM else False)

    def _log_profiling_info(self, process_result):
        """
        Shows profiling and specific information in logger.

        Args:
            process_result (dict): result from Accelerator.process_file
        """
        # Skip method if logger not at least on INFO Level
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
