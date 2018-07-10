# coding=utf-8
"""apyfal._utilities.security tests"""

import pytest


def test_asymmetric_cipher():
    """Tests AsymmetricCipher"""
    from apyfal._utilities.security import AsymmetricCipher
    from apyfal.exceptions import ClientSecurityException

    # Tests new cipher
    cipher_private = AsymmetricCipher()

    # Tests cipher from public key
    cipher_public = AsymmetricCipher(cipher_private.public_key)
    assert cipher_private.public_key == cipher_public.public_key

    # Tests cipher from public and private keys
    cipher_private_public = AsymmetricCipher(
        public_key=cipher_private.public_key,
        private_key=cipher_private.private_key)
    assert cipher_private.public_key == cipher_private_public.public_key
    assert cipher_private.private_key == cipher_private_public.private_key

    # Tests encrypt/decrypt
    message = 'Unencrypted message'
    encrypted = cipher_public.encrypt(message)
    assert message != encrypted
    decrypted = cipher_private.decrypt(encrypted)
    assert decrypted == message

    # Tests encrypt/decrypt with bad key
    with pytest.raises(ClientSecurityException):
        AsymmetricCipher().decrypt(encrypted)

    # Tests signature
    signature = cipher_private.sign(message)
    cipher_public.verify(signature, message)

    # Tests signature with bad key
    bad_signature = AsymmetricCipher().sign(message)
    with pytest.raises(ClientSecurityException):
        cipher_public.verify(bad_signature, message)


def test_symmetric_cipher():
    """Tests SymmetricCipher"""
    from apyfal._utilities.security import SymmetricCipher
    from apyfal.exceptions import ClientSecurityException

    # Tests new cipher
    cipher = SymmetricCipher()

    # Tests cipher from key
    assert SymmetricCipher(cipher.key).key == cipher.key

    # Tests encrypt/decrypt
    message = 'Unencrypted message'
    encrypted = cipher.encrypt(message)
    assert message != encrypted
    decrypted = cipher.decrypt(encrypted)
    assert decrypted == message

    # Tests encrypt/decrypt with bad key
    with pytest.raises(ClientSecurityException):
        SymmetricCipher().decrypt(encrypted)
