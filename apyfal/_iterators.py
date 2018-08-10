# coding=utf-8
"""Accelerator iterators"""
import re

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
            object.__setattr__(self, name, value)
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
        return self._properties['_repr']

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


def iter_accelerators(config=None, instance_name_prefix=True, **filters):
    """
    Iterates over accelerators.

    Args:
        config (apyfal.configuration.Configuration, path-like object or
            file-like object):
            If not set, will search it in current working directory,
            in current user "home" folder. If none found, will use default
            configuration values.
            Path-like object can be path, URL or cloud object URL.
        instance_name_prefix (bool or str): If True,
            use "instance_name_prefix" from configuration, if False
            don't filter by prefix, if str, uses this str as prefix
        filters: Arguments names are host properties to filter,
            values are regular expressions.

    Returns:
        generator: Accelerator generator
    """
    # Get configuration
    config = _cfg.create_configuration(config)

    # Initializes filters
    for attr, pattern in filters.items():
        filters[attr] = re.compile(pattern).match

    def is_valid(host_dict):
        """Validates host.

        Args:
            host_dict (dict): Host

        Returns:
            bool: True if host is valid
        """
        for key, match in filters:
            if not match(host_dict[key]):
                return False
        return True

    host_type_match = filters.get('host_type')

    # List available host_types
    host_types = set()
    host_types.add(config['host']['host_type'])
    for section in config:
        if section.startswith('host.'):
            host_type = section.split('.', 1)[1]
            if host_type_match is None or host_type_match(host_type):
                host_types.add(host_type)

    # Yield accelerators for each host_type
    for host_type in host_types:
        # Instantiates basic host to use it as searcher
        try:
            searcher = Host(host_type=host_type, config=config)
        except (_exc.HostException, TypeError):
            continue

        # Caches repr base
        repr = "<%s.%s" % (searcher.__class__.__module__,
                           searcher.__class__.__name__) + ' %s>'
        repr_list = [(name, attr.lstrip('_')) for name, attr in searcher._REPR]

        # Iterates over hosts found for this host_type
        for host in searcher.iter_hosts(instance_name_prefix):
            # Filters host
            if not is_valid(host):
                continue

            # Adds host repr
            host['_repr'] = repr % (' '.join(
                "%s='%s'" % (name, host.get(attr)) for name, attr in repr_list
                if host.get(attr) is not None))

            # Yields lazy accelerators
            yield _LazyAccelerator(host_properties=host, config=config)
