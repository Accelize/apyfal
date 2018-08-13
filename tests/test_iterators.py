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
