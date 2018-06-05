# coding=utf-8
"""apyfal tests

"pytest" required

Marks can be used to filter test to run:

    run only tests with "mymark"
        pytest -v -m mymark

    run alls tests except "mymark"
        pytest -v -m "not mymark"

Marks are added to test with decorator

    @pytest.mark.mymark
    def test_myfunction()
        ...

Available marks:
    need_csp: Require a CSP to run.
    need_csp_alibaba: Require Alibaba host to run.
    need_csp_aws: Require AWS host to run.
    need_csp_ovh: Require OVH host to run.
    need_accelize: Require Accelize server
"""
