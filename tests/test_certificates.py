# coding=utf-8
"""apyfal._certificates tests"""


def test_self_signed_certificate():
    """Tests _certificates.self_signed_certificate"""
    from apyfal._certificates import (
        self_signed_certificate, get_host_names_from_certificate,
        create_wildcard_certificate)

    # Test result are bytes with BEGIN and END
    cert, key = self_signed_certificate(
        "127.0.0.1", "127.0.0.2", common_name='host_name', country_name='FR')

    assert b'BEGIN CERTIFICATE' in cert
    assert b'END CERTIFICATE' in cert
    assert b'BEGIN RSA PRIVATE KEY' in key
    assert b'END RSA PRIVATE KEY' in key
    assert get_host_names_from_certificate(cert) == ["127.0.0.1", "127.0.0.2"]

    cert = create_wildcard_certificate(common_name='host_name')[0]
    assert get_host_names_from_certificate(cert) == ["*"]
