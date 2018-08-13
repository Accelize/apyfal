# coding=utf-8
"""Accelerator iterators"""
import re
from concurrent.futures import ThreadPoolExecutor

from apyfal.host import Host
import apyfal.configuration as _cfg
import apyfal.exceptions as _exc


class _LazyClass:
    """
    Class that get attributes from cached dict or
    from real accelerator
    """

    def __setattr__(self, name, value):
        # Set privates variables locally
        if name.startswith('_'):
            # Python 2 don't support object.__setattr__(self, name, value)
            self.__dict__[name] = value
            return

        # Tries to set other names on real accelerator
        setattr(self._get_accelerator_object(True), name, value)

    def __getattr__(self, item):
        # If accelerator instantiated, redirects getattr to it
        if self._get_accelerator_object() is not None:
            return getattr(self._get_accelerator_object(), item)

        # If not, tries to get information from properties
        try:
            return self._properties[item]

        # If not in properties, instantiates accelerator and get
        # attribute from it
        except KeyError:
            return getattr(self._get_accelerator_object(True), item)

    def __str__(self):
        return str(self._get_accelerator_object() or self._properties['_repr'])

    __repr__ = __str__


class _LazyMember(_LazyClass):
    """Lazy proxy class that represent Accelerator member

    Args:
        properties (dict): Member properties.
        get_accelerator_object (function): Get accelerator function.
    """

    def __init__(self, properties, get_accelerator_object):
        self._get_accelerator_object = get_accelerator_object
        self._properties = properties


class _LazyAccelerator(_LazyClass):
    """Accelerator proxy that store information and lazy instantiates
    accelerator if needed.

    Allows to iterate over accelerators and getting some base
    information without losing time to instantiates them.

    But, if needed, instantiates accelerator to provides its public interfaces.

    Args:
        host_properties (dict): Host properties directory.
        config (apyfal.configuration.Configuration): Configuration.
    """

    def __init__(self, host_properties, config):
        self._accelerator_object = None

        # Get accelerator keyword arguments
        self._accelerator_kwargs = dict(
            accelerator=host_properties['accelerator'], config=config,
            stop_mode='keep', host_type=host_properties['host_type'])
        if 'instance_id' in host_properties:
            self._accelerator_kwargs[
                'instance_id'] = host_properties['instance_id']

        # Generates client properties
        client_properties = dict(
            name=host_properties['accelerator'],
            _repr="<apyfal.client.Client accelerator='%s'>" %
                  host_properties['accelerator'])

        if 'url' in host_properties:
            # Remote clients
            client_properties['url'] = host_properties['url']
            client_properties['_repr'] = (
                client_properties['_repr'].rstrip('>') +
                " url='%s'>" % host_properties['url'])

        # Generates accelerator members
        self._properties = dict(
            host=_LazyMember(host_properties, self._get_accelerator_object),
            client=_LazyMember(client_properties, self._get_accelerator_object),
            _repr="<apyfal.Accelerator client=(%s) host=(%s)>" % (
                client_properties['_repr'], host_properties['_repr']))

    def _get_accelerator_object(self, force_real_one=False):
        """
        Lazy instantiates accelerator.

        Args:
            force_real_one (bool): Forces to instantiate real accelerator if
                not already instantiated.

        Returns:
            apyfal.Accelerator
        """
        if self._accelerator_object is None and force_real_one:
            # Can't import it at top level
            from apyfal import Accelerator

            # Instantiates accelerator
            self._accelerator_object = Accelerator(**self._accelerator_kwargs)
        return self._accelerator_object


def _is_valid(host_dict, filters):
    """Validates host.

    Args:
        host_dict (dict): Host
        filters (dict): Dict of re.match filters.

    Returns:
        bool: True if host is valid
    """
    for key, match in filters.items():
        if not match(host_dict[key]):
            return False
    return True


def _get_host_iter(host_type, config, instance_name_prefix):
    """
    Get hosts generator for the specified host_type

    Args:
        host_type (str): host type
        config (apyfal.configuration.Configuration): Configuration.
        instance_name_prefix (bool or str): see iter_accelerators
            instance_name_prefix

    Returns:
        generator: Hosts generator
    """
    try:
        return Host(host_type=host_type, config=config).iter_hosts(
            instance_name_prefix)
    except _exc.HostException:
        return iter(())


def iter_accelerators(config=None, instance_name_prefix=True, **filters):
    """
    Iterates over all accelerators available on remote hosts.

    Args:
        config (apyfal.configuration.Configuration, path-like object or
            file-like object):
            If not set, will search it in current working directory,
            in current user "home" folder. If none found, will use default
            configuration values.
            Path-like object can be path, URL or cloud object URL.
        instance_name_prefix (bool or str): If True,
            use "instance_name_prefix" from configuration; if False
            don't filter by prefix; if str, uses this str as prefix
        filters: Arguments names are host properties to filter,
            values are regular expressions.

    Returns:
        generator: Accelerators generator
    """
    # Get configuration
    config = _cfg.create_configuration(config)

    # Initializes filters
    for attr, pattern in filters.items():
        filters[attr] = re.compile(pattern).match

    host_type_match = filters.get('host_type')

    # List available host_types
    host_types = set()
    host_types.add(config['host']['host_type'])
    for section in config:
        if section.startswith('host.'):
            host_type = section.split('.', 1)[1]
            if host_type_match is None or host_type_match(host_type):
                host_types.add(host_type)

    # Gets information for each host_type
    futures = []
    with ThreadPoolExecutor(max_workers=len(host_types)) as executor:
        for host_type in host_types:
            futures.append(executor.submit(
                _get_host_iter, host_type, config, instance_name_prefix))

    # Yields lazy accelerators that match filters
    for future in futures:
        for host in future.result():
            if _is_valid(host, filters):
                yield _LazyAccelerator(host_properties=host, config=config)
