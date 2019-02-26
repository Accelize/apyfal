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
__version__ = "1.2.6"
__copyright__ = "Copyright 2018 Accelize"
__licence__ = "Apache 2.0"
__all__ = ['Accelerator', 'AcceleratorPoolExecutor', 'iter_accelerators',
           'get_logger']

from sys import version_info as _py
if (_py[0] < 2) or (_py[0] == 2 and _py[1] < 7) or (_py[0] == 3 and _py[1] < 4):
    from sys import version
    raise ImportError('Python %s is not supported by Apyfal' % version)
del _py

from concurrent.futures import ThreadPoolExecutor as _ThreadPoolExecutor, \
    wait as _wait

import apyfal.host as _hst
import apyfal.client as _clt
import apyfal.exceptions as _exc
import apyfal.configuration as _cfg
from apyfal._utilities import (
    get_logger as _get_logger, memoizedmethod as _memoizedmethod)
from apyfal._iterators import iter_accelerators
from apyfal._pool_executor import (
    AcceleratorPoolExecutor, _AbstractAsyncAccelerator)


# Makes get_logger available here for easy access
get_logger = _get_logger


class Accelerator(_AbstractAsyncAccelerator):
    """
    This class provides the full accelerator features by handling
    Accelerator and its host.

    Args:
        accelerator (str): Name of the accelerator to initialize,
            to know the accelerator list please visit
            "https://accelstore.accelize.com".
        config (apyfal.configuration.Configuration, path-like object or file-like object):
            If not set, will search it in current working directory,
            in current user "home" folder. If none found, will use default
            configuration values.
            Path-like object can be path, URL or cloud object URL.
        accelize_client_id (str): Accelize Client ID.
            Client ID is part of the access key generated on
            "https:/accelstore.accelize.com/user/applications".
        accelize_secret_id (str): Accelize Secret ID. Secret ID come with
            xlz_client_id.
        host_type (str): Type of host to use.
        host_ip (str): IP or URL address of an already existing host to use.
            If not specified, create a new host.
        stop_mode (str or int): Host stop mode.
            Default to 'term' if new host, or 'keep' if already existing host.
            See "apyfal.host.Host.stop_mode" property for more
            information and possible values.
        prefer_self_hosted (bool): Default to True.
            If True, and current machine is an accelerator host, operates this
            accelerator instead of instantiating a new accelerator host.
            If current machine is not an accelerator host, instantiates a new
            host normally.
        host_kwargs: Keyword arguments related to specific host. See targeted
            host class to see full list of arguments.
    """
    # Number of parallel workers
    _WORKERS_COUNT = 8

    def __init__(self, accelerator=None, config=None, accelize_client_id=None,
                 accelize_secret_id=None, host_type=None, host_ip=None,
                 stop_mode=None, prefer_self_hosted=None, **host_kwargs):

        # Initialize some variables
        self._cache = {}
        self._tasks_count = 0
        self._tasks = set()
        self._cleaning_up = False
        self._stopped = False

        # Initialize configuration
        config = _cfg.create_configuration(config)

        # Create host object
        host_type, is_local = self._get_host(
            config, host_type, prefer_self_hosted)

        if not is_local:
            # Use a remote host
            self._host = _hst.Host(
                host_type=host_type, config=config, host_ip=host_ip,
                stop_mode=stop_mode, **host_kwargs)

            # Remote control use REST client
            client_type = 'REST'

            # Get updated URL if any
            try:
                host_ip = self._host.url
            except _exc.HostException:
                host_ip = None

            # Get certificate if any
            try:
                ssl_cert_crt = self._host.ssl_cert_crt
            except AttributeError:
                ssl_cert_crt = None

        else:
            # Use local host
            self._host = None
            ssl_cert_crt = None

            # Use default local client if not specified IP
            client_type = 'REST' if (host_ip and host_type is None) else None

        # Create AcceleratorClient object
        self._client = _clt.AcceleratorClient(
            accelerator=accelerator, client_type=client_type,
            accelize_client_id=accelize_client_id, host_ip=host_ip,
            accelize_secret_id=accelize_secret_id, config=config,
            ssl_cert_crt=ssl_cert_crt, host_type=host_type,
            region=host_kwargs.get('region'))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.__del__()

    def __del__(self):
        if self._stopped:
            return

        self._stopped = True
        self._cleaning_up = True
        try:
            self.stop()
        finally:
            self._cleaning_up = False

    def __str__(self):
        return "<%s.%s client=(%s) host=(%s)>" % (
            self.__class__.__module__, self.__class__.__name__,
            str(self._client).strip('<>'), str(
                self._host if host is not None else 'localhost').strip('<>'))

    __repr__ = __str__

    @property
    def client(self):
        """
        Accelerator client.

        Returns:
            apyfal.client.AcceleratorClient: Accelerator client
        """
        return self._client

    @property
    def host(self):
        """
        Accelerator host.

        Returns:
            apyfal.host.Host subclass: Host
        """
        return self._host

    @property
    @_memoizedmethod
    def _workers(self):
        """
        Worker threads pool.

        Returns:
            concurrent.future.ThreadPoolExecutor
        """
        return _ThreadPoolExecutor(max_workers=self._WORKERS_COUNT)

    @property
    def process_running_count(self):
        """
        Return number of asynchronous process tasks running or pending.

        Returns:
            int: count.
        """
        return self._tasks_count

    def _set_task_done(self, future):
        """
        Remove task from running count.

        Only for use as callback.

        Args:
            future (concurrent.futures.Future): Calling future.
        """
        self._tasks_count -= 1
        self._tasks.discard(future)

    def _wait_completed(self):
        """
        Wait async tasks are completed or cancelled.
        """
        _wait(self._tasks.copy())

    def start(self, stop_mode=None, src=None, info_dict=None,
              host_env=None, reload=None, reset=None, **parameters):
        """
        Starts and/or configure an accelerator.

        Args:
            stop_mode (str or int): Host stop mode. If not None, override
                current "stop_mode" value. See "apyfal.host.Host.stop_mode"
                property for more information and possible values.
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
                with extra information from operation.
            host_env (dict): Overrides Accelerator "env".
        """
        if self._host is not None:
            # Start host if needed (Do nothing if already started)
            self._host.start(accelerator=self._client.name, stop_mode=stop_mode)

            # Set accelerator URL to host URL
            self._client.url = self._host.url

            # Get environment
            host_env = self._host.get_configuration_env(**(host_env or dict()))

        # Configure accelerator if needed
        return self._client.start(
            src=src, host_env=host_env or dict(), info_dict=info_dict,
            reload=reload, reset=reset, **parameters)

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
        _enable_logger = _get_logger().isEnabledFor(20)
        if _enable_logger and info_dict is None:
            info_dict = dict()

        # Process file with accelerator
        process_result = self._client.process(
            src=src, dst=dst, info_dict=info_dict, **parameters)

        if _enable_logger:
            self._log_profiling_info(info_dict)
        return process_result

    def process_submit(self, src=None, dst=None, info_dict=None,
                       **parameters):
        """
        Schedules the process operation to be executed and returns a Future
        object representing the execution.

        See "apyfal.Accelerator.process"

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
                The dict will be updated on task completion.

        Returns:
            concurrent.futures.Future: Future object representing execution.
                See "apyfal.Accelerator.process" method for "Future.result()"
                content.
        """
        # Submits process
        future = self._workers.submit(self.process, src=src, dst=dst,
                                      info_dict=info_dict, **parameters)

        # Keeps track of running tasks (Or planned in queue)
        self._tasks_count += 1
        self._tasks.add(future)
        future.add_done_callback(self._set_task_done)

        # Returns future
        return future

    def stop(self, stop_mode=None, info_dict=None):
        """
        Stop accelerator session and accelerator host depending of the
        parameters

        Args:
            stop_mode (str or int): Host stop mode. If not None, override
                current "stop_mode" value. See "apyfal.host.Host.stop_mode"
                property for more information and possible values.
            info_dict (dict or None): If a dict passed, this dict is updated
                with extra information from current operation.
        """
        # Waits all tasks are completed before allowing to stop accelerator
        self._wait_completed()

        # Updates stop mode
        if self._host is not None:
            self._host.stop_mode = stop_mode
            stop_mode = self._host.stop_mode

        # Stops accelerator, performs full stop only if not in "keep" mode
        try:
            return self._client.stop(
                info_dict=info_dict,
                full_stop=False if (stop_mode == 'keep' and self._cleaning_up)
                else True)

        except (AttributeError, _exc.ClientException):
            return None

        # Stops host
        finally:
            if self._host is not None:
                try:
                    self._host.stop(stop_mode)
                except (AttributeError, _exc.HostException):
                    pass

    @staticmethod
    def _get_host(config, host_type, prefer_self_hosted):
        """
        Determinate if use local host or host specified by host type.

        Args:
            config (apyfal.configuration.Configuration): Configuration.
            host_type (str or None): Host type.
            prefer_self_hosted (bool or None): Prefer localhost is available.

        Returns:
            tuple: host type, is local
        """
        host_type = host_type or config['host']['host_type']

        if prefer_self_hosted is None:
            prefer_self_hosted = config['host']['prefer_self_hosted']
        if prefer_self_hosted is None:
            prefer_self_hosted = True

        is_local = (host_type in (None, 'localhost') or (
                prefer_self_hosted and _cfg.accelerator_executable_available()))

        return host_type, is_local

    @staticmethod
    def _log_profiling_info(info_dict):
        """
        Shows profiling and specific information in logger.

        Args:
            info_dict (dict): info_dict from AcceleratorClient.process
        """
        # Handle profiling info
        try:
            profiling = info_dict['app']['profiling']
        except (KeyError, TypeError):
            return None

        logger = _get_logger()
        logger.info("Profiling information from result:")

        # Compute and show information only on DEBUG level
        values = dict()

        for key in ('wall-clock-time', 'fpga-elapsed-time',
                    'total-bytes-written', 'total-bytes-read'):
            try:
                values[key] = float(profiling[key])
            except KeyError:
                pass

        total_bytes = (values.get('total-bytes-written', 0.0) +
                       values.get('total-bytes-read', 0.0))
        global_time = values.get('wall-clock-time', 0.0)
        fpga_time = values.get('fpga-elapsed-time', 0.0)

        if global_time > 0.0:
            logger.info('- Wall clock time: %.3fs' % global_time)

        if fpga_time > 0.0:
            logger.info('- FPGA elapsed time: %.3fs' % fpga_time)

        if total_bytes > 0.0 and global_time > 0.0:
            logger.info("- Server processing bandwidths: %.1f MB/s",
                        total_bytes / global_time / 1024.0 / 1024.0)

        if total_bytes > 0.0 and fpga_time > 0.0:
            logger.info("- FPGA processing bandwidths: %.1f MB/s",
                        total_bytes / fpga_time / 1024.0 / 1024.0)
