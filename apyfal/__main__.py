#! /usr/bin/env python
#  coding=utf-8
"""Provides Command line use of Apyfal"""

_ACCELERATOR_CACHE = '~/.apyfal/command_line/accelerators'


class _CommandLineException(Exception):
    """Exceptions from command line mode"""


def _cached_accelerator(name, action, accelerator=None):
    """
    Cache accelerator instance.

    Args:
        name (str): --name argument value
        action (str): dump, load, delete
        accelerator (apyfal.Accelerator):
            Accelerator to dump.

    Returns:
        apyfal.Accelerator): loaded accelerator.
    """
    import pickle
    import os

    cache_dir = os.path.expanduser(_ACCELERATOR_CACHE)
    cached_file = os.path.join(cache_dir, name)

    # Dump cache
    if action == 'dump':
        # Ensure directory exists
        from apyfal._utilities import makedirs
        makedirs(cache_dir, exist_ok=True)

        # Dump Accelerator object
        with open(cached_file, 'wb') as file:
            pickle.dump(accelerator, file)

    # Load cache
    elif action == 'load':
        if os.path.isfile(cached_file):
            with open(cached_file, 'rb') as file:
                return pickle.load(file)
        raise _CommandLineException((
            'No accelerator found for "--name %s"'
            'Please run "apyfal create" command before'
            ' use other commands.') % name)

    # Delete cache
    else:
        try:
            os.remove(cached_file)
        except OSError:
            pass


def _handle_command(func):
    """Decorator that print function result if any
    and properly format exceptions.

    Args:
        func: Function

    Returns:
        Decorated function
    """
    def patched(*args, **kwargs):
        """Call function and print result"""
        try:
            result = func(*args, **kwargs)
        except _CommandLineException as exception:
            print('error: %s' % exception.args[0])
            return

        if result:
            print(result)

    return patched


def _get_accelerator(name, save=False, parameters=None):
    """
    Instantiate apyfal.Accelerator.

    Args:
        name (str): --name argument value
        save (bool): If True, save instance, else load it.
        parameters (dict): apyfal.Accelerator parameters.

    Returns:
        apyfal.Accelerator: Accelerator instance.
    """
    # Load cached accelerator
    if not save:
        return _cached_accelerator(name, 'load')

    # Instantiate accelerator
    from apyfal import Accelerator
    accelerator = Accelerator(**parameters)

    # Cache accelerator
    _cached_accelerator(name, 'dump', accelerator)


def _action_create(parameters):
    """
    First instantiation and configuration of
    apyfal.Accelerator.

    Args:
        parameters (dict):
            apyfal.Accelerator parameters.
    """
    name = parameters.pop('name')
    _get_accelerator(name=name, save=True,
                     parameters=parameters)


@_handle_command
def _action_start(parameters):
    """
    Call apyfal.Accelerator.start

    Args:
        parameters (dict):
            apyfal.Accelerator.start parameters.

    Returns:
        dict: apyfal.Accelerator.start result.
    """
    name = parameters.pop('name')
    return _get_accelerator(name=name).start(**parameters)


@_handle_command
def _action_process(parameters):
    """
    Call apyfal.Accelerator.process

    Args:
        parameters (dict):
            apyfal.Accelerator.process parameters.

    Returns:
        dict: apyfal.Accelerator.process result.
    """
    name = parameters.pop('name')
    return _get_accelerator(name=name).process(**parameters)


@_handle_command
def _action_stop(parameters):
    """
    Call apyfal.Accelerator.stop

    Args:
        parameters (dict):
            apyfal.Accelerator.stop parameters.

    Returns:
        dict: apyfal.Accelerator.stop result.
    """
    # Stop accelerator
    name = parameters.pop('name')
    result = _get_accelerator(name=name).stop(**parameters)

    # Clears cache
    _cached_accelerator(name, 'delete')

    # Returns result
    return result


def _action_copy(parameters):
    """
    Call apyfal.storage.copy

    Args:
        parameters (dict):
            apyfal.storage.copy parameters.
    """
    from apyfal.storage import copy
    copy(**parameters)


def _action_clear():
    """Clear cache"""
    import os
    import shutil
    shutil.rmtree(
        os.path.expanduser(_ACCELERATOR_CACHE),
        ignore_errors=True)


def _run_command():
    """
    Command line entry point
    """
    from argparse import ArgumentParser

    # Initialize some values
    command_dest = 'Apyfal command'
    epilog_base = (
        'Extra parameters can be passed '
        'as "--parameter_name=parameter_value". ')
    name_arg = dict(
        help='Load Accelerator with this name that '
             'was created with "create" commands',
        default='default')

    # Create command line argument parser
    parser = ArgumentParser(
        prog='apyfal', description='Apyfal command line utility.')
    sub_parsers = parser.add_subparsers(
        required=True, dest=command_dest, title='Commands',
        description='Apyfal must perform one of the following commands:',
        help='Apyfal commands')

    # apyfal.Accelerator()
    description = 'Create accelerator and configure host.'
    action = sub_parsers.add_parser(
        'create', help=description, description=description,
        epilog=epilog_base + (
            'See Apyfal documentation for information on possible '
            'parameters for the targeted host '
            '(https://apyfal.readthedocs.io/). '
            'See accelerator documentation for '
            'information on its parameters'))
    action.add_argument(
        '--name', '-n',
        help='Save Accelerator with this name, '
             'it can be called later with "start", '
             '"process" and "stop" commands and '
             '"--name" argument.',
        default='default'
    )
    action.add_argument('--accelerator', '-a')
    action.add_argument('--config', '-c')
    action.add_argument('--accelize_client_id')
    action.add_argument('--accelize_secret_id')
    action.add_argument('--host_type')
    action.add_argument('--host_ip')
    action.add_argument('--stop_mode')

    # apyfal.Accelerator.start()
    description = 'Start and configure Accelerator.'
    action = sub_parsers.add_parser(
        'start', help=description, description=description,
        epilog=epilog_base + (
            'See accelerator documentation for '
            'information on specific configuration parameters'))
    action.add_argument('--name', '-n', **name_arg)
    action.add_argument('--stop_mode')
    action.add_argument('--datafile', '-i')
    action.add_argument('--info_dict', action='store_true')
    action.add_argument('--parameters', '-j')

    # apyfal.Accelerator.process()
    description = 'Process with Accelerator.'
    action = sub_parsers.add_parser(
        'process', help=description, description=description,
        epilog=epilog_base + (
            'See accelerator documentation for '
            'information on specific process parameters'))
    action.add_argument('--name', '-n', **name_arg)
    action.add_argument('--file_in', '-i')
    action.add_argument('--file_out', '-o')
    action.add_argument('--info_dict', action='store_true')
    action.add_argument('--parameters', '-j')

    # apyfal.Accelerator.stop()
    description = 'Stop accelerator.'
    action = sub_parsers.add_parser(
        'stop', help=description, description=description)
    action.add_argument('--name', '-n', **name_arg)
    action.add_argument('--info_dict', action='store_true')

    # apyfal.storage.copy()
    description = 'Copy Apyfal Storage URL.'
    action = sub_parsers.add_parser(
        'copy', help=description, description=description)
    action.add_argument('source')
    action.add_argument('destination')

    # Clear cache function
    description = 'Clear cached accelerators.'
    sub_parsers.add_parser(
        'clear', help=description, description=description)

    # Parse known arguments
    namespace, extra_args = parser.parse_known_args()
    kwargs = vars(namespace)

    # Get command name
    command = kwargs.pop(command_dest)

    # Parser unknown arguments
    parameter = None
    value = None
    for arg in extra_args:

        # --parameter=value
        if arg.startswith('-') and '=' in arg:
            arg, value = arg.split('=', 1)

        # --parameter
        if arg.startswith('-'):
            parameter = arg.lstrip('-').strip()

        # value
        else:
            value = arg.strip()

        # Save value
        if parameter and value:
            # Space separated value
            if parameter in kwargs:
                kwargs[parameter] += ' %s' % value

            # Simple value
            else:
                kwargs[parameter] = value

        value = None

    # Run command
    globals()['_action_%s' % command](kwargs)


# Run command if called directly
if __name__ == '__main__':
    _run_command()
