# coding=utf-8
"""apyfal._iterators tests"""


def test_lazy_accelerator():
    """Tests _LazyAccelerator"""
    from apyfal._iterators import _LazyAccelerator
    import apyfal

    # Initializes some values
    config = apyfal.configuration.Configuration()
    accelerator = 'accelerator'
    host_type = 'host_type'
    instance_id = 'instance_id'
    url = 'url'
    _repr = '_repr'

    # Mocks accelerator
    class Accelerator:
        """Dummy Accelerator"""
        attribute = 1

        def __init__(self, **kwargs):
            """Checks arguments"""
            assert kwargs == dict(
                accelerator=accelerator, config=config, stop_mode='keep',
                host_type=host_type, instance_id=instance_id)

    apyfal_accelerator = apyfal.Accelerator
    apyfal.Accelerator = Accelerator

    # Tests
    try:
        host_properties = dict(
            accelerator=accelerator, host_type=host_type,
            instance_id=instance_id,
            url=url, _repr=_repr)
        acc = _LazyAccelerator(host_properties, config)
        assert acc._accelerator_object is None

        assert acc.host.instance_id == instance_id
        assert acc._accelerator_object is None

        assert repr(acc) != repr(acc._accelerator_object)
        assert acc._accelerator_object is None

        assert acc.attribute == 1
        assert acc._accelerator_object is not None

        acc.attribute = 0
        assert acc._accelerator_object.attribute == 0
        assert acc.attribute == 0
        assert repr(acc) == repr(acc._accelerator_object)

    # Restore Accelerator
    finally:
        apyfal.Accelerator = apyfal_accelerator


def test_iter_accelerators():
    """Tests iter_accelerators"""
    from apyfal._iterators import iter_accelerators, _LazyAccelerator
    import apyfal.host
    from apyfal.exceptions import HostRuntimeException

    # Initializes some values
    dummy_config = apyfal.configuration.Configuration()
    for section in tuple(dummy_config):
        if 'host' in section:
            try:
                del dummy_config._sections[section]
            except KeyError:
                continue

    dummy_config['host']['host_type'] = 'include_selected'
    dummy_config['host.include_subsection']['key'] = '0'
    dummy_config['host.include_errored']['key'] = '0'
    dummy_config['host.exclude']['key'] = '0'
    dummy_prefix = 'prefix'
    dummy_filters = dict(host_type='include_*', host_name='0')

    # Mocks Host
    class Host:
        """Dummy Host"""

        def __init__(self, config=None, host_type=None, **_):
            """Checks arguments"""
            assert config == dummy_config
            self.host_type = host_type
            if 'errored' in host_type:
                raise HostRuntimeException('Error')

        def iter_hosts(self, host_name_prefix):
            """Checks arguments and yields fake values"""
            assert host_name_prefix == dummy_prefix
            for host in range(2):
                yield dict(host_type=self.host_type, host_name=str(host),
                           accelerator='accelerator', _repr='_repr')

    apyfal_host_host = apyfal.host.Host
    apyfal._iterators.Host = Host
    apyfal.host.Host = Host

    # Tests
    try:
        result = list(iter_accelerators(
            config=dummy_config, host_name_prefix=dummy_prefix,
            **dummy_filters))
        assert len(result) == 2
        for index, item in enumerate(result):
            assert isinstance(item, _LazyAccelerator)
            assert 'include' in item.host._properties['host_type']

    # Restore Host
    finally:
        apyfal.host.Host = apyfal_host_host
        apyfal._iterators.Host = apyfal_host_host
