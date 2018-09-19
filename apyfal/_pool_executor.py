# coding=utf-8
"""concurrent.futures like Accelerator pool executor"""
from abc import abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
from time import time

import apyfal.exceptions as _exc
from apyfal._utilities import ABC


class AbstractAsyncAccelerator(ABC):
    """
    Asynchronous Accelerator process interface.
    """

    @abstractmethod
    def process_submit(self, file_in=None, file_out=None, info_dict=False,
                       **parameters):
        """

        Abstract method for asynchronous "process" method

        See "apyfal.Accelerator.process" for more information.
        """

    def process_map(self, files_in=None, files_out=None, info_dict=False,
                    timeout=None, **parameters):
        """
        Map process execution on multiples files.

        Args:
            files_in (iterable of path-like object or file-like object):
                Iterable of input files to process.
                Path-like object can be path, URL or cloud object URL.
            files_out (iterable of path-like object or file-like object):
                Iterable of output files.
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
            concurrent.futures.Future: Future object representing execution.
        """
        # Based on "concurrent.futures.Executor.map"

        # Initializes timeout
        if timeout is not None:
            end_time = timeout + time()

        # Get file count
        try:
            size_in = len(files_in)
        except TypeError:
            size_in = 0

        try:
            size_out = len(files_out)
        except TypeError:
            size_out = 0

        if size_in and size_out and size_in != size_out:
            raise _exc.ClientConfigurationException(
                '"files_in" and "files_out" must contain the same count of'
                ' files.')

        # Submit process
        futures = []
        for index in range(size_in or size_out):
            try:
                file_in = files_in[index]
            except IndexError:
                file_in = None
            try:
                file_out = files_out[index]
            except IndexError:
                file_out = None

            futures.append(self.process_submit(
                file_in=file_in, file_out=file_out, info_dict=info_dict,
                **parameters))

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


class AcceleratorPoolExecutor(AbstractAsyncAccelerator):
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
        host_ip (str): IP or URL address of an already existing host to use.
            If not specified, create a new host.
        stop_mode (str or int): Host stop mode.
            Default to 'term' if new host, or 'keep' if already existing host.
            See "apyfal.host.Host.stop_mode" property for more
            information and possible values.
        workers_count (int): Number of accelerator workers.
        host_kwargs: Keyword arguments related to specific host. See targeted
            host class to see full list of arguments.
    """

    def __init__(self, accelerator=None, config=None, accelize_client_id=None,
                 accelize_secret_id=None, host_type=None, host_ip=None,
                 stop_mode='term', workers_count=4, **host_kwargs):

        # Needs to lazy import to avoid importing issues
        from apyfal import Accelerator

        # Initializes Accelerators workers
        self._workers_count = workers_count
        with ThreadPoolExecutor(max_workers=self._workers_count) as executor:
            self._workers = [executor.submit(
                Accelerator, accelerator=accelerator, config=config,
                accelize_client_id=accelize_client_id,
                accelize_secret_id=accelize_secret_id, host_type=host_type,
                host_ip=host_ip, stop_mode=stop_mode,
                **host_kwargs) for _ in range(workers_count)]

        # TODO: host_ip, instance_id => lists + properties

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.stop()

    def __del__(self):
        self.stop()

    # TODO: repr

    def start(self, stop_mode=None, datafile=None, info_dict=False,
              host_env=None, **parameters):
        """
        Starts and/or configure all accelerators in the pool.

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
            list: List of "Accelerator.start" results.
        """
        with ThreadPoolExecutor(max_workers=self._workers_count) as executor:
            futures = [executor.submit(
                worker.start, stop_mode=stop_mode, datafile=datafile,
                info_dict=info_dict, host_env=host_env,
                **parameters) for worker in self._workers]
        return [future.result() for future in as_completed(futures)]

    def process_submit(self, file_in=None, file_out=None, info_dict=False,
                       **parameters):
        """
        Schedules the process operation to be executed and returns a Future
        object representing the execution.

        See "apyfal.Accelerator.process".

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
                See "apyfal.Accelerator.process" method for
                "Future.result()" content.
        """
        # Find less busy worker
        workers_task_count = [
            worker.process_running_count for worker in self._workers]
        index = workers_task_count.index(min(workers_task_count))

        # Submit work to it.
        return self._workers[index].process_submit(
            file_in=file_in, file_out=file_out, info_dict=info_dict,
            **parameters)

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
