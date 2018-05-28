# coding=utf-8
"""acceleratorAPI.client tests"""


def test_timeout():
    """Tests Timeout"""
    from acceleratorAPI._utilities import Timeout

    # Should not timeout
    with Timeout(timeout=1, sleep=0.001) as timeout:
        while True:
            assert not timeout.reached()
            break

    # Should timeout
    with Timeout(timeout=0.0) as timeout:
        while True:
            assert timeout.reached()
            break
