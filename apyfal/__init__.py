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
__version__ = "1.2.0"
__copyright__ = "Copyright 2018 Accelize"
__licence__ = "Apache 2.0"
__all__ = ['Accelerator', 'AcceleratorPoolExecutor', 'iter_accelerators',
           'get_logger']

from sys import version_info as _py
if (_py[0] < 2) or (_py[0] == 2 and _py[1] < 7) or (_py[0] == 3 and _py[1] < 4):
    from sys import version
    raise ImportError('Python %s is not supported by Apyfal' % version)

from concurrent.futures import ThreadPoolExecutor as _ThreadPoolExecutor

import apyfal.host as _hst
import apyfal.client as _clt
import apyfal.exceptions as _exc
import apyfal.configuration as _cfg
from apyfal._utilities import (
    get_logger as _get_logger, memoizedmethod as _memoizedmethod)
from apyfal._iterators import iter_accelerators
from apyfal._pool_executor import AcceleratorPoolExecutor, \
    AbstractAsyncAccelerator as _AbstractAsyncAccelerator


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
        host_kwargs: Keyword arguments related to specific host. See targeted
            host class to see full list of arguments.
    """
    def __init__(self, accelerator=None, config=None, accelize_client_id=None,
                 accelize_secret_id=None, host_type=None, host_ip=None,
                 stop_mode='term', **host_kwargs):
        # Initialize some variables
        self._cache = {}
        self._tasks_count = 0

        # Initialize configuration
        config = _cfg.create_configuration(config)

        # Create host object
        host_type = host_type or config['host']['host_type']
        if host_type not in (None, 'localhost'):
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
        else:
            # Use local host
            self._host = None

            # Use default local client if not specified IP
            client_type = 'REST' if (host_ip and host_type is None) else None

        # Create AcceleratorClient object
        self._client = _clt.AcceleratorClient(
            accelerator=accelerator, client_type=client_type,
            accelize_client_id=accelize_client_id, host_ip=host_ip,
            accelize_secret_id=accelize_secret_id, config=config)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.stop()

    def __del__(self):
        self.stop()

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
        return _ThreadPoolExecutor()

    @property
    def process_running_count(self):
        """
        Return number of asynchronous process tasks running.

        Returns:
            int: count.
        """
        return self._tasks_count

    def _set_task_done(self):
        """
        Remove task from running count.
        """
        self._tasks_count -= 1

    def start(self, stop_mode=None, datafile=None, info_dict=False,
              host_env=None, **parameters):
        """
        Starts and/or configure an accelerator.

        Args:
            stop_mode (str or int): Host stop mode. If not None, override
                current "stop_mode" value. See "apyfal.host.Host.stop_mode"
                property for more information and possible values.
            datafile (path-like object or file-like object): Depending on the
                accelerator, a configuration data file need to be loaded before
                a process can be run.
                Path-like object can be path, URL or cloud object URL.
            info_dict (bool): If True, returns a dict containing information on
                configuration operation.
            parameters (str, path-like object or dict):
                Accelerator configuration specific
                parameters Can also be a full configuration parameters
                dictionary (Or JSON equivalent as str literal or apyfal.storage
                URL to file) Parameters dictionary override default
                configuration values, individuals specific parameters overrides
                parameters dictionary values. Take a look to accelerator
                documentation for more information on possible parameters.
                Path-like object can be path, URL or cloud object URL.

        Returns:
            dict: Optional, only if "info_dict" is True. AcceleratorClient
                response. AcceleratorClient contain output information from
                configuration operation. Take a look to accelerator
                documentation for more information.
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
            datafile=datafile, host_env=host_env or dict(), info_dict=info_dict,
            **parameters)

    def process(self, file_in=None, file_out=None, info_dict=False,
                **parameters):
        """
        Processes with accelerator.

        Args:
            file_in (path-like object or file-like object):
                Input file to process.
                Path-like object can be path, URL or cloud object URL.
            file_out (path-like object or file-like object):
                Output processed file.
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
            info_dict (bool): If True, returns a dict containing information on
                process operation.

        Returns:
            dict: Result from process operation, depending used accelerator.
            dict: Optional, only if "info_dict" is True. AcceleratorClient
                response. AcceleratorClient contain output information from
                process operation. Take a look accelerator documentation for
                more information.
        """
        _enable_logger = _get_logger().isEnabledFor(20)

        # Process file with accelerator
        process_result = self._client.process(
            file_in=file_in, file_out=file_out,
            info_dict=info_dict or _enable_logger, **parameters)

        if _enable_logger:
            # Logger case
            self._log_profiling_info(process_result)
            return process_result if info_dict else process_result[0]
        return process_result

    def process_submit(self, file_in=None, file_out=None, info_dict=False,
                       **parameters):
        """
        Schedules the process operation to be executed and returns a Future
        object representing the execution.

        See "apyfal.Accelerator.process"

        Args:
            file_in (path-like object or file-like object):
                Input file to process.
                Path-like object can be path, URL or cloud object URL.
            file_out (path-like object or file-like object):
                Output processed file.
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
            info_dict (bool): If True, returns a dict containing information on
                process operation.

        Returns:
            concurrent.futures.Future: Future object representing execution.
                See "apyfal.Accelerator.process" method for "Future.result()"
                content.
        """
        # Submits process
        future = self._workers.submit(
            self.process, file_in=file_in, file_out=file_out,
            info_dict=info_dict, **parameters)

        # Keeps track of running tasks (Or planned in queue)
        self._tasks_count += 1
        future.add_done_callback(self._set_task_done)

        # Returns future
        return future

    def stop(self, stop_mode=None, info_dict=False):
        """
        Stop accelerator session and accelerator host depending of the
        parameters

        Args:
            stop_mode (str or int): Host stop mode. If not None, override
                current "stop_mode" value. See "apyfal.host.Host.stop_mode"
                property for more information and possible values.
            info_dict (bool): If True, returns a dict containing information on
                stop operation.

        Returns:
            dict: Optional, only if "info_dict" is True. AcceleratorClient
                response. AcceleratorClient contain output information from
                stop operation. Take a look to accelerator documentation for
                more information.
        """
        # Updates stop mode
        if self._host is not None:
            self._host.stop_mode = stop_mode
            stop_mode = self._host.stop_mode

        # Stops accelerator, performs full stop only if not in "keep" mode
        try:
            return self._client.stop(
                info_dict=info_dict,
                full_stop=False if stop_mode == 'keep' else True)

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
    def _log_profiling_info(process_result):
        """
        Shows profiling and specific information in logger.

        Args:
            process_result (dict): result from AcceleratorClient.process
        """
        logger = _get_logger()

        try:
            app = process_result[1]['app']
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

            if global_time > 0.0:
                logger.info('- FPGA elapsed time: %.3fs' % fpga_time)

            if total_bytes > 0.0 and global_time > 0.0:
                logger.info("- Server processing bandwidths: %.1f MB/s",
                            total_bytes / global_time / 1024.0 / 1024.0)

            if total_bytes > 0.0 and fpga_time > 0.0:
                logger.info("- FPGA processing bandwidths: %.1f MB/s",
                            total_bytes / fpga_time / 1024.0 / 1024.0)

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
