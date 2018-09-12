# coding=utf-8
"""apyfal.__main__ tests"""
from collections import namedtuple

import pytest


def test_cached_accelerator(tmpdir):
    """Tests _cached_accelerator"""
    from apyfal.__main__ import _cached_accelerator
    import apyfal.__main__ as main

    name = 'accelerator'
    parameters = {'param1': 1, 'param2': 2}
    cache_dir = tmpdir.join('cache')

    # Mock cache dir
    old_cache_dir = main._ACCELERATOR_CACHE
    main._ACCELERATOR_CACHE = str(cache_dir)

    # Tests
    try:
        # Dumps accelerator
        assert not cache_dir.check()
        _cached_accelerator(
            name=name, action='dump', parameters=parameters)
        assert cache_dir.join(name).check()

        # Loads
        assert _cached_accelerator(
            name=name, action='load') == parameters

        assert _cached_accelerator(name='not_exists', action='load') == {}

        # Delete
        _cached_accelerator(name=name, action='delete')
        assert not cache_dir.join(name).check()

        assert not cache_dir.join('not_exists').check()
        _cached_accelerator(name='not_exists', action='delete')

    # Restore cache dir
    finally:
        main._ACCELERATOR_CACHE = old_cache_dir


def test_handle_command():
    """Tests _handle_command"""
    from apyfal.__main__ import _handle_command, _CommandLineException

    result = 'result'
    raises_exceptions = False

    # Mocks parser and command function
    class ArgumentParser:

        @staticmethod
        def exit(message=None):
            """Checks arguments"""
            assert not raises_exceptions
            if result:
                assert message == result
            else:
                assert message is None

        @staticmethod
        def error(message):
            """Checks arguments"""
            assert raises_exceptions
            assert message == result

    dummy_parser = ArgumentParser()
    dummy_args = (1, 2, 3)
    dummy_kwargs = {'arg1': 1, 'arg2': 2}

    def command(parser, *args, **kwargs):
        """Checks arguments and returns result"""
        assert args == dummy_args
        assert kwargs == dummy_kwargs
        assert parser is dummy_parser
        if raises_exceptions:
            raise _CommandLineException(result)
        return result

    patched = _handle_command(command)

    # Tests command success
    patched(dummy_parser, *dummy_args, **dummy_kwargs)

    # Tests command success and returns empty result
    result = ''
    patched(dummy_parser, *dummy_args, **dummy_kwargs)

    # Tests command fail
    raises_exceptions = True
    patched(dummy_parser, *dummy_args, **dummy_kwargs)


def test_get_accelerator(tmpdir):
    """Tests _get_accelerator"""
    from apyfal.__main__ import _get_accelerator, _CommandLineException
    import apyfal.__main__ as main
    import apyfal

    name = 'accelerator'
    parameters = {'instance_id': '123',
                  'accelerator': 'accelerator'}
    cache_dir = tmpdir.join('cache')
    raise_exception = False

    # Mock cache dir and Accelerator
    old_cache_dir = main._ACCELERATOR_CACHE
    main._ACCELERATOR_CACHE = str(cache_dir)

    class Accelerator:
        """Dummy Accelerator"""

        def __init__(self, *_, **kwargs):
            """Checks arguments"""
            if raise_exception:
                raise apyfal.exceptions.AcceleratorException
            assert kwargs == parameters

    apyfal_accelerator = apyfal.Accelerator
    apyfal.Accelerator = Accelerator
    # Tests
    try:
        # Create accelerator
        accelerator = _get_accelerator(
            name, action='create', parameters=parameters)
        assert isinstance(accelerator, Accelerator)

        # Load accelerator
        accelerator = _get_accelerator(name, action='load')
        assert isinstance(accelerator, Accelerator)

        # Load accelerator
        accelerator = _get_accelerator(name, action='update')
        assert isinstance(accelerator, Accelerator)

        # Load not cached accelerator (But can be instantiated without create)
        parameters = {}
        accelerator = _get_accelerator('Not_exists_but_ok', action='load')
        assert isinstance(accelerator, Accelerator)

        # Load not cached accelerator (But fail to instantiate without create)
        raise_exception = True
        with pytest.raises(_CommandLineException):
            _get_accelerator('Not_Exists', action='load')

        # Re-raise exception on create
        with pytest.raises(apyfal.exceptions.AcceleratorException):
            _get_accelerator('Fail_to_create', action='create',
                             parameters=parameters)

    # Restore cache dir
    finally:
        main._ACCELERATOR_CACHE = old_cache_dir
        apyfal.Accelerator = apyfal_accelerator


def test_parse_and_run():
    """Tests _parse_and_run"""
    from apyfal.__main__ import (
        _parse_and_run, _COMMAND_DEST)
    import apyfal.__main__ as main
    from argparse import ArgumentParser
    import sys

    # Mocks action and parser
    dummy_parser = ArgumentParser()
    sub_parsers = dummy_parser.add_subparsers(
        dest=_COMMAND_DEST)
    sub_parser = sub_parsers.add_parser('dummy')
    sub_parser.add_argument('--known')

    def dummy_action(parser, kwargs):
        """Checks arguments"""
        assert parser is dummy_parser
        assert kwargs == {
            'known': 'known_value',
            'unknown': 'unknown_value',
            'equal': 'equal_value',
            'spaced': 'value1 value2',
            'spaced_equal': 'value3 value4'}

    argv = sys.argv
    main._action_dummy = dummy_action

    # Tests
    try:
        # Command with all kind of arguments
        sys.argv = [
            '', 'dummy',
            '--known', 'known_value',
            '--unknown', 'unknown_value',
            '--equal=equal_value',
            '--spaced', 'value1', 'value2',
            '--spaced_equal=value3', 'value4']
        _parse_and_run(dummy_parser)

        # No command
        sys.argv = ['']
        with pytest.raises(SystemExit):
            _parse_and_run(dummy_parser)

    # Removes Mocked action
    finally:
        del main._action_dummy
        sys.argv = argv


def test_run_command():
    """Tests _run_command"""
    from apyfal.__main__ import _run_command
    import apyfal.__main__ as main
    from argparse import ArgumentParser

    # Mocks _parse_and_run

    def parse_and_run(parser):
        """Checks parser"""
        assert isinstance(parser, ArgumentParser)

    main_parse_and_run = main._parse_and_run
    main._parse_and_run = parse_and_run

    # Tests
    try:
        _run_command()

    # Restores mocked function
    finally:
        main._parse_and_run = main_parse_and_run


def test_actions(tmpdir):
    """Tests _action_* functions"""
    import apyfal.__main__ as main

    dummy_name = 'name'
    dummy_parameters = {'arg1': 1, 'arg2': 2}
    full_parameters = dummy_parameters.copy()
    full_parameters['name'] = dummy_name

    # Mocks accelerator and parser

    Host = namedtuple('Host', ('url', 'key_pair'))

    class Accelerator:

        host = Host(url='http://url', key_pair='key_pair')

        @staticmethod
        def start(**kwargs):
            """Checks parameters"""
            assert kwargs == dummy_parameters

        @staticmethod
        def process(**kwargs):
            """Checks parameters"""
            assert kwargs == dummy_parameters

        @staticmethod
        def stop(**kwargs):
            """Checks parameters"""
            assert kwargs == dummy_parameters

    def _get_accelerator(
            name=None, action='load', parameters=None, **_):
        """Checks parameters and returns fake result"""
        assert name == dummy_name

        if action == 'create':
            assert parameters is not None
            assert parameters['stop_mode'] == 'keep'
        else:
            assert parameters is None

        return Accelerator()

    class ArgumentParser:

        @staticmethod
        def exit(*_, **__):
            """Do nothing"""

        @staticmethod
        def error(*_, **__):
            """Do nothing"""

    parser = ArgumentParser()
    cache_dir = tmpdir.join('cache')

    main_get_accelerator = main._get_accelerator
    main._get_accelerator = _get_accelerator
    old_cache_dir = main._ACCELERATOR_CACHE
    main._ACCELERATOR_CACHE = str(cache_dir)

    # Tests
    try:
        # Accelerator functions
        main._action_create(parser, full_parameters.copy())
        main._action_start(parser, full_parameters.copy())
        main._action_process(parser, full_parameters.copy())
        main._action_stop(parser, full_parameters.copy())

        # Host without URL
        Accelerator.host = None
        main._action_create(parser, full_parameters.copy())
        main._action_start(parser, full_parameters.copy())

        # Cache cleanup
        cache_dir.join(dummy_name).ensure()
        main._action_clear(parser, full_parameters.copy())
        assert not cache_dir.check()

        # Storage function
        source = tmpdir.join("source")
        source.ensure()
        destination = tmpdir.join("destination")
        assert not destination.check()
        assert source.check()
        main._action_copy(parser, {
            'source': str(source),
            'destination': str(destination)})
        assert destination.check()

    # Restores mocked things
    finally:
        main._get_accelerator = main_get_accelerator
        main._ACCELERATOR_CACHE = old_cache_dir
