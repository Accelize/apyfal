# coding=utf-8
"""apyfal._utilities.security tests"""

import pytest


def test_asymmetric_cipher():
    """Tests AsymmetricCipher"""
    from apyfal._utilities.security import AsymmetricCipher

    # Tests new cipher
    cipher_private = AsymmetricCipher()

    # Tests cipher from public key
    cipher_public = AsymmetricCipher(cipher_private.public_key)
    assert cipher_private.public_key == cipher_public.public_key

    # Tests encrypt/decrypt
    message = 'Unencrypted message'
    encrypted = cipher_public.encrypt(message)
    assert message != encrypted
    decrypted = cipher_private.decrypt(encrypted)
    assert decrypted == message

    # Tests encrypt/decrypt with bad key
    with pytest.raises(ValueError):
        AsymmetricCipher().decrypt(encrypted)

    # Tests signature
    signature = cipher_private.sign(message)
    assert cipher_public.verify(signature, message)

    # Tests signature with bad key
    bad_signature = AsymmetricCipher().sign(message)
    assert not cipher_public.verify(bad_signature, message)
