# coding=utf-8
"""apyfal._pool_executor tests"""
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from time import sleep

import pytest


def test_abstract_async_accelerator_process_map():
    """Tests _AbstractAsyncAccelerator.process_map"""
    from apyfal._pool_executor import _AbstractAsyncAccelerator
    from apyfal.exceptions import ClientConfigurationException

    # Mocks sub class
    files_in = []
    files_out = []
    process_kwargs = dict(arg='arg', info_dict=True, parameters='parameters')
    process_duration = 0.0

    class AsyncAccelerator(_AbstractAsyncAccelerator):
        """Mocked sub class"""

        def __init__(self):
            self._executor = ThreadPoolExecutor(max_workers=4)

        @staticmethod
        def run_task():
            """Dummy task"""
            sleep(process_duration)
            return True

        def process_submit(self, src=None, dst=None, **kwargs):
            """Checks arguments and returns fake result"""
            assert kwargs == process_kwargs
            assert src in files_in or (src is None and not files_in)
            assert dst in files_out or (dst is None and not files_out)
            return self._executor.submit(self.run_task)

    acc = AsyncAccelerator()

    # Test: Empty
    assert list(acc.process_map()) == []

    # Test: One file in
    files_in = ['0']
    assert list(acc.process_map(srcs=files_in, **process_kwargs)) == [True]
    files_in = []

    # Test: One file out
    files_out = ['0']
    assert list(acc.process_map(
        dsts=files_out, **process_kwargs)) == [True]
    files_out = []

    # Test: Multiples files in
    files_in = ['0', '1', '2', '3']
    assert list(acc.process_map(
        srcs=files_in, **process_kwargs)) == [True] * len(files_in)
    files_in = []

    # Test: Multiples files out
    files_out = ['0', '1', '2', '3']
    assert list(acc.process_map(
        dsts=files_out, **process_kwargs)) == [True] * len(files_out)
    files_out = []

    # Test: Multiples files in and out
    files_in = ['i0', 'i1', 'i2', 'i3']
    files_out = ['o0', 'o1', 'o2', 'o3']
    assert list(acc.process_map(
        srcs=files_in, dsts=files_out,
        **process_kwargs)) == [True] * len(files_out)

    # Test: count mismatch
    files_in = files_in[:-1]
    with pytest.raises(ClientConfigurationException):
        acc.process_map(
            srcs=files_in, dsts=files_out, **process_kwargs)
    files_in = ['i0', 'i1', 'i2', 'i3']

    # Test: timeout
    process_duration = 0.05
    with pytest.raises(TimeoutError):
        list(acc.process_map(
            srcs=files_in, dsts=files_out, timeout=0.001,
            **process_kwargs))


def test_accelerator_pool_executor():
    """Tests AcceleratorPoolExecutor"""
    import apyfal

    accelerator = 'accelerator'
    workers_count = 4
    start_kwargs = dict(src='src',
                        host_env='env', stop_mode='term', reset=None,
                        reload=None)
    stop_kwargs = dict(stop_mode=None)
    process_kwargs = dict(arg='arg', info_dict=None, parameters='parameters',
                          src='src', dst='dst')

    # Mocks Accelerator

    class Future:
        """Mocked future"""

        @staticmethod
        def result():
            """Return fake result"""
            return True

    class Accelerator:
        """Mocked accelerator"""
        client = 'client'
        host = 'host'

        def __init__(self, *_, **__):
            """Do nothing"""
            self.process_running_count = 0
            self.running = False

        def _wait_completed(self):
            """Do Nothing"""

        def start(self, **kwargs):
            """Checks arguments and return fake result"""
            self.running = True
            assert kwargs == start_kwargs
            return True

        def process_submit(self, **kwargs):
            """Checks arguments and return fake result"""
            assert kwargs == process_kwargs
            self.process_running_count += 1
            return Future()

        def stop(self, **kwargs):
            """Checks arguments and return fake result"""
            self.running = False
            assert kwargs == stop_kwargs
            return True

    apyfal_accelerator = apyfal.Accelerator
    apyfal.Accelerator = Accelerator

    # Tests
    try:

        # Instantiation
        pool = apyfal.AcceleratorPoolExecutor(
            accelerator=accelerator, workers_count=workers_count)
        assert len(pool.accelerators) == workers_count
        for acc in pool.accelerators:
            assert isinstance(acc, Accelerator)
        for host in pool.hosts:
            assert host == Accelerator.host
        for client in pool.clients:
            assert client == Accelerator.client

        assert accelerator in str(pool)
        assert str(workers_count) in str(pool)

        # Start
        for acc in pool.accelerators:
            assert not acc.running

        assert pool.start(**start_kwargs) == [True] * workers_count

        for acc in pool.accelerators:
            assert acc.running

        # Process and checks tasks balancing
        for _ in range(workers_count * 2):
            assert pool.process_submit(**process_kwargs).result() is True
        assert [acc.process_running_count for acc in pool.accelerators] == \
               [2] * workers_count

        # Stop and wait
        assert pool.stop(wait=True, **stop_kwargs) == [True] * workers_count

        for acc in pool.accelerators:
            assert not acc.running

        # Stop and don't wait
        for acc in pool.accelerators:
            acc.running = True

        futures = pool.stop(wait=False, **stop_kwargs)

        assert len(futures) == workers_count
        for future in futures:
            assert future.result() is True

        for acc in pool.accelerators:
            assert not acc.running

        # With
        with apyfal.AcceleratorPoolExecutor(
                workers_count=workers_count) as pool:
            pool.start(**start_kwargs)
            for acc in pool.accelerators:
                assert acc.running
        for acc in pool.accelerators:
            assert not acc.running

    # Restores mocked class
    finally:
        apyfal.Accelerator = apyfal_accelerator
