# coding=utf-8
"""concurrent.futures like Accelerator pool executor"""
from abc import abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
from time import time

import apyfal.exceptions as _exc
from apyfal.configuration import create_configuration
from apyfal._utilities import ABC


class _AbstractAsyncAccelerator(ABC):
    """
    Asynchronous Accelerator process interface.
    """

    @abstractmethod
    def process_submit(self, src=None, dst=None, info_dict=False,
                       **parameters):
        """

        Abstract method for asynchronous "process" method

        See "apyfal.Accelerator.process" for more information.
        """

    def process_map(self, srcs=None, dsts=None, info_dict=False,
                    timeout=None, **parameters):
        """
        Map process execution on multiples files.

        Args:
            srcs (iterable of path-like object or file-like object):
                Iterable of input data to process.
                Must be an iterable of "src" parameters of the "process" method.
                Path-like object can be path, URL or cloud object URL.
            dsts (iterable of path-like object or file-like object):
                Iterable of output data.
                Must be an iterable of "dst" parameters of the "process" method.
                Path-like object can be path, URL or cloud object URL.
            timeout (float): The maximum number of seconds to wait. If None,
                then there is no limit on the wait time.
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
            generator of concurrent.futures.Future: Future object representing
                execution.

        Raises:
            concurrent.futures.TimeoutError: "timeout" reached on at least one
                task.
        """
        # Based on "concurrent.futures.Executor.map"

        # Initializes timeout
        if timeout is not None:
            end_time = timeout + time()

        # Get file count
        src = dst = None
        if srcs is not None:
            size_src = len(srcs)
        else:
            size_src = 0

        if dsts is not None:
            size_dst = len(dsts)
        else:
            size_dst = 0

        if size_src and size_dst and size_src != size_dst:
            raise _exc.ClientConfigurationException(
                '"files_in" and "files_out" must contain the same count of'
                ' files.')

        # Submit process
        futures = []
        for index in range(size_src or size_dst):
            if size_src:
                src = srcs[index]
            if size_dst:
                dst = dsts[index]

            futures.append(self.process_submit(
                src=src, dst=dst, info_dict=info_dict, **parameters))

        def result_iterator():
            """
            Yield must be hidden in closure so that the futures are submitted
            before the first iterator value is required.
            """
            try:
                # reverse to keep finishing order
                futures.reverse()
                while futures:
                    # Careful not to keep a reference to the popped future
                    if timeout is None:
                        yield futures.pop().result()
                    else:
                        yield futures.pop().result(end_time - time())
            finally:
                for future in futures:
                    future.cancel()

        return result_iterator()


class AcceleratorPoolExecutor(_AbstractAsyncAccelerator):
    """
    An executor that uses a pool of workers_count identically configured
    accelerator to execute calls asynchronously.

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
        stop_mode (str or int): Host stop mode.
            Default to 'term' if new host, or 'keep' if already existing host.
            See "apyfal.host.Host.stop_mode" property for more
            information and possible values.
        workers_count (int): Number of accelerator workers.
        host_kwargs: Keyword arguments related to specific host. See targeted
            host class to see full list of arguments.
    """

    def __init__(self, accelerator=None, config=None, accelize_client_id=None,
                 accelize_secret_id=None, host_type=None,
                 stop_mode='term', workers_count=4, **host_kwargs):

        # Uses a common configuration file
        config = create_configuration(config)

        # Needs to lazy import to avoid importing issues
        from apyfal import Accelerator

        # Initializes Accelerators workers
        self._accelerator = accelerator
        self._workers_count = workers_count
        self._workers = [Accelerator(
            accelerator=accelerator, config=config,
            accelize_client_id=accelize_client_id,
            accelize_secret_id=accelize_secret_id, host_type=host_type,
            stop_mode=stop_mode, **host_kwargs) for _ in range(workers_count)]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.stop()

    def __del__(self):
        self.stop()

    def __str__(self):
        return "<apyfal.%s accelerator='%s' workers=%s>" % (
            self.__class__.__name__, self._accelerator, self._workers_count)

    __repr__ = __str__

    @property
    def accelerators(self):
        """
        Accelerator workers.

        Returns:
            list of apyfal.Accelerator: Accelerators
        """
        return self._workers

    @property
    def clients(self):
        """
        Accelerator workers clients.

        Returns:
            list of apyfal.client.AcceleratorClient: Clients
        """
        return [worker.client for worker in self._workers]

    @property
    def hosts(self):
        """
        Accelerator workers hosts.

        Returns:
            list of apyfal.host.Host subclass: Hosts
        """
        return [worker.host for worker in self._workers]

    def start(self, stop_mode=None, src=None, info_dict=False, host_env=None,
              reload=None, reset=None, **parameters):
        """
        Starts and/or configure all accelerators in the pool.

        Args:
            stop_mode (str or int): Host stop mode. If not None, override
                current "stop_mode" value. See "apyfal.host.Host.stop_mode"
                property for more information and possible values.
            src (path-like object or file-like object): Depending on the
                accelerator, a configuration data need to be loaded before
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
            reload (bool): Force reload of FPGA bitstream.
            reset (bool): Force reset of FPGA logic.
            host_env (dict): Overrides Accelerator "env".

        Returns:
            list: List of "Accelerator.start" results.
        """
        with ThreadPoolExecutor(max_workers=self._workers_count) as executor:
            futures = [executor.submit(
                worker.start, stop_mode=stop_mode, src=src,
                info_dict=info_dict, host_env=host_env, reload=reload,
                reset=reset, **parameters) for worker in self._workers]
        return [future.result() for future in as_completed(futures)]

    def process_submit(self, src=None, dst=None, info_dict=False,
                       **parameters):
        """
        Schedules the process operation to be executed and returns a Future
        object representing the execution.

        See "apyfal.Accelerator.process".

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
            info_dict (bool): If True, returns a dict containing information on
                process operation.

        Returns:
            concurrent.futures.Future: Future object representing execution.
                See "apyfal.Accelerator.process" method for
                "Future.result()" content.
        """
        # Find less busy worker
        workers_task_count = [
            worker.process_running_count for worker in self._workers]
        index = workers_task_count.index(min(workers_task_count))

        # Submit work to it.
        return self._workers[index].process_submit(
            src=src, dst=dst, info_dict=info_dict, **parameters)

    def stop(self, stop_mode=None, info_dict=False, wait=True):
        """
        Signal the executor that it should free any resources that it is using
        when the currently pending futures are done executing. Calls to
        process_submit() and process_map() made after shutdown will raise
        RuntimeError.

        Stop each accelerator session and accelerator host depending of the
        parameters

        Args:
            stop_mode (str or int): Host stop mode. If not None, override
                current "stop_mode" value. See "apyfal.host.Host.stop_mode"
                property for more information and possible values.
            info_dict (bool): If True, returns a dict containing information on
                stop operation.
            wait (bool): Waits stop completion before return.

        Returns:
            list: List of "Accelerator.stop" results if "info_dict", else
                list of Futures objects.
        """
        with ThreadPoolExecutor(max_workers=self._workers_count) as executor:
            futures = [executor.submit(
                worker.stop, stop_mode=stop_mode, info_dict=info_dict)
                for worker in self._workers]

        if wait:
            return [future.result() for future in as_completed(futures)]
        return futures
