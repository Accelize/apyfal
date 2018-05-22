# coding=utf-8
"""acceleratorAPI.ovh tests"""

import pytest
from tests.test_csp___init__ import run_full_real_test_sequence


@pytest.mark.need_csp
@pytest.mark.need_csp_ovh
def test_ovhclass_real():
    """OVHClass in real case"""
    from acceleratorAPI.configuration import Configuration

    # Skip if configuration not with OVH
    config = Configuration()
    if config.get_default('csp', 'provider') != 'OVH':
        pytest.skip('Need OVH configuration.')

    # Test: Full generic sequence
    run_full_real_test_sequence(config)
