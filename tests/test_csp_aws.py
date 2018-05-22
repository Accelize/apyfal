# coding=utf-8
"""acceleratorAPI.csp.aws tests"""

import pytest
from tests.test_csp___init__ import run_full_real_test_sequence


@pytest.mark.need_csp
@pytest.mark.need_csp_aws
def test_ovhclass_real():
    """AWSClass in real case"""
    from acceleratorAPI.configuration import Configuration

    # Skip if configuration not with AWS
    config = Configuration()
    if config.get_default('csp', 'provider') != 'AWS':
        pytest.skip('Need AWS configuration.')

    # Test: Full generic sequence
    run_full_real_test_sequence(config)
