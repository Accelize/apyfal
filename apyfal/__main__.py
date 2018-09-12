#! /usr/bin/env python
#  coding=utf-8
"""Provides Command line use of Apyfal"""

_ACCELERATOR_CACHE = '~/.apyfal/command_line/accelerators'
_COMMAND_DEST = 'Apyfal command'


class _CommandLineException(Exception):
    """Exceptions from command line mode"""


def _cached_accelerator(name, action, parameters=None):
    """
    Cache accelerator instance.

    Args:
        name (str): --name argument value
        action (str): dump, load, delete
        parameters (dict): Accelerator parameters to dump

    Returns:
        dict: loaded Accelerator parameters.
    """
    from json import dump, load
    from os.path import expanduser, isfile, join

    cache_dir = expanduser(_ACCELERATOR_CACHE)
    cached_file = join(cache_dir, name)

    # Dumps cache
    if action == 'dump':
        # Ensures directory exists
        from apyfal._utilities import makedirs
        makedirs(cache_dir, exist_ok=True)

        # Dumps Accelerator object
        with open(cached_file, 'wt') as file:
            dump(parameters, file)

    # Loads cache
    elif action == 'load':
        if isfile(cached_file):
            with open(cached_file, 'rt') as file:
                return load(file)
        # Returns empty configuration if not file found
        return dict()

    # Deletes cache
    elif action == 'delete':
        from os import remove
        try:
            remove(cached_file)
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
    def patched(parser, *args, **kwargs):
        """Call function and print result

        Args:
            parser (argparse.ArgumentParser): Argument parser
            args, kwargs: Function arguments.
        """
        from apyfal.exceptions import AcceleratorException

        # Runs function
        try:
            result = func(parser, *args, **kwargs)

        # Prints error and set status code using parser
        except (_CommandLineException,
                AcceleratorException) as exception:
            parser.error(str(exception))
            return

        # Returns result using parser
        parser.exit(message=result if result else None)

    return patched


def _get_accelerator(name, action='load', parameters=None,
                     accelerator=None):
    """
    Instantiate apyfal.Accelerator.

    Args:
        name (str): --name argument value
        action (str): 'load', 'create' or 'update".
        parameters (dict): apyfal.Accelerator parameters.
        accelerator (apyfal.Accelerator): Accelerator.

    Returns:
        apyfal.Accelerator: Accelerator instance.
    """
    # Loads cached accelerator
    if action in ('load', 'update'):
        parameters = _cached_accelerator(name, 'load')

    # Instantiates accelerator
    if accelerator is None:
        from apyfal import Accelerator, get_logger, exceptions

        # Shows logger
        get_logger(True)

        # Tries to instantiates accelerator
        try:
            accelerator = Accelerator(**parameters)

        # Raises special exception if accelerator not created previously
        except exceptions.AcceleratorException:
            if action != 'create':
                raise _CommandLineException((
                    'No accelerator found for "--name %s"'
                    'Please run "apyfal create" command before'
                    ' use other commands.') % name)
            raise

    # Caches accelerator
    if action in ('create', 'update'):
        for attribute, key in (
                ('host_type', 'host_type'),
                ('url', 'host_ip'),
                ('instance_id', 'instance_id')):
            try:
                parameters[key] = getattr(
                    accelerator.host, attribute)
            except AttributeError:
                continue

        _cached_accelerator(name, 'dump', parameters)

    # Returns accelerator
    return accelerator


@_handle_command
def _action_create(_, parameters):
    """
    First instantiation and configuration of
    apyfal.Accelerator.

    Args:
        parameters (dict):
            apyfal.Accelerator parameters.
    """
    name = parameters.pop('name')
    parameters['stop_mode'] = 'keep'
    _get_accelerator(
        name=name, action='create', parameters=parameters)


@_handle_command
def _action_start(_, parameters):
    """
    Call apyfal.Accelerator.start

    Args:
        parameters (dict):
            apyfal.Accelerator.start parameters.

    Returns:
        dict: apyfal.Accelerator.start result.
    """
    name = parameters.pop('name')
    accelerator = _get_accelerator(name=name)
    result = accelerator.start(**parameters)

    # Updates cached accelerator
    _get_accelerator(
        name=name, action='update', accelerator=accelerator)

    # Shows Accelerator information
    try:
        ip_address = accelerator.host.url
        if ip_address is not None and '://' in ip_address:
            ip_address = ip_address.split('://')[1].strip('/')
        key_pair = accelerator.host.key_pair
    except AttributeError:
        return result
    return 'Accelerator IP address: %s\nSSH key pair: %s%s' % (
        ip_address, key_pair, ('\n\n%s' % result) if result else '')


@_handle_command
def _action_process(_, parameters):
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
def _action_stop(_, parameters):
    """
    Call apyfal.Accelerator.stop

    Args:
        parameters (dict):
            apyfal.Accelerator.stop parameters.

    Returns:
        dict: apyfal.Accelerator.stop result.
    """
    # Stops accelerator
    name = parameters.pop('name')
    result = _get_accelerator(name=name).stop(**parameters)

    # Clears cache
    _cached_accelerator(name, 'delete')

    # Returns result
    return result


@_handle_command
def _action_copy(_, parameters):
    """
    Call apyfal.storage.copy

    Args:
        parameters (dict):
            apyfal.storage.copy parameters.
    """
    from apyfal.storage import copy
    copy(**parameters)


def _action_clear(*_):
    """Clear cache"""
    from os.path import expanduser
    from shutil import rmtree
    rmtree(expanduser(_ACCELERATOR_CACHE), ignore_errors=True)


def _parse_and_run(parser):
    """
    Parse arguments and run function.

    Args:
        parser (argparse.ArgumentParser): Argument parser
    """
    # Parses known arguments
    namespace, extra_args = parser.parse_known_args()
    kwargs = vars(namespace)

    # Gets command name
    command = kwargs.pop(_COMMAND_DEST)
    if not command:
        parser.error('An Apyfal command is required')

    # Parsers unknown arguments
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

        # Saves value
        if parameter and value:
            # Space separated value
            if parameter in kwargs:
                kwargs[parameter] += ' %s' % value

            # Simple value
            else:
                kwargs[parameter] = value

        value = None

    # Adds parent directory to sys.path:
    # Allows import of Apyfal if this script is run locally
    import sys
    from os.path import abspath, dirname
    sys.path.insert(
        0, dirname(dirname(abspath(__file__))))

    # Runs command
    globals()['_action_%s' % command](parser, kwargs)


def _run_command():
    """
    Command line entry point
    """
    from argparse import ArgumentParser, SUPPRESS
    from warnings import filterwarnings

    # Disables Python warnings
    filterwarnings("ignore")

    # Initializes some values
    epilog_base = (
        'Extra parameters can be passed '
        'as "--parameter_name=parameter_value". ')
    name_arg = dict(
        help='Load Accelerator with this name that '
             'was created with "create" commands',
        default='default')

    # Creates command line argument parser
    parser = ArgumentParser(
        prog='apyfal', description='Apyfal command line utility.')
    sub_parsers = parser.add_subparsers(
        dest=_COMMAND_DEST, title='Commands',
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
    action.add_argument('--stop_mode', default='keep', help=SUPPRESS)

    # apyfal.Accelerator.start()
    description = 'Start and configure Accelerator.'
    action = sub_parsers.add_parser(
        'start', help=description, description=description,
        epilog=epilog_base + (
            'See accelerator documentation for '
            'information on specific configuration parameters'))
    action.add_argument('--name', '-n', **name_arg)
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
    action.add_argument('--stop_mode', default='term')

    # apyfal.storage.copy()
    description = 'Copy a file using Apyfal.storage.'
    action = sub_parsers.add_parser(
        'copy', help=description, description=description)
    action.add_argument('source')
    action.add_argument('destination')

    # Clears cache function
    description = 'Clear cached accelerators.'
    sub_parsers.add_parser(
        'clear', help=description, description=description)

    # Parse arguments and run
    _parse_and_run(parser)


# Run command if called directly
if __name__ == '__main__':
    _run_command()
