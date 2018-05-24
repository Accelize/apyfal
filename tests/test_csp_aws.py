# coding=utf-8
"""acceleratorAPI.csp.aws tests"""

import pytest
from tests.test_csp___init__ import run_full_real_test_sequence


@pytest.mark.need_csp
@pytest.mark.need_csp_aws
def test_ovhclass_real():
    """AWSClass in real case"""
    run_full_real_test_sequence('AWS', {

    })
