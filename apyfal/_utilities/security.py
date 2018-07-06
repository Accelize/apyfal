# coding=utf-8
"""Generic security utilities"""
import base64

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature


class AsymmetricCipher:
    """Asymmetric cipher for encryption and signature.

    Args:
        public_key (str): Public key in PEM format.
            If not specified, a new key pair will be generated.
    """

    def __init__(self, public_key=None):
        self._private_key = None
        self._public_key = None

        # Generate new key pair if not exists
        if not public_key:
            self._private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend())
            self._public_key = self._private_key.public_key()

        # Load public key
        else:
            self._public_key = serialization.load_pem_public_key(
                public_key.encode(), backend=default_backend())

    # Public key only functions

    @property
    def public_key(self):
        """Public key

        Returns:
            str: Public key in PEM format.
        """
        return self._public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo).decode()

    def encrypt(self, message):
        """
        Encrypt with public key.

        Args:
            message (str): Message to encrypt

        Returns:
            str: encrypted message
        """
        encrypted = self._public_key.encrypt(
            message.encode(), *self._encryption_parameters())
        return base64.urlsafe_b64encode(encrypted).decode()

    def verify(self, signature, message):
        """
        Verify signature with public key.

        Args:
            signature (str): Signature
            message (str): Signed message

        Returns:
            bool: True if signature match.
        """
        signature = base64.urlsafe_b64decode(signature.encode())
        try:
            self._public_key.verify(
                signature, message.encode(),
                *self._signature_parameters())
        except InvalidSignature:
            return False
        return True

    # Private key only functions

    def decrypt(self, encrypted):
        """
        Decrypt message with private key.

        Args:
            encrypted (str): Encrypted message

        Returns:
            str: Decrypted message
        """
        encrypted = base64.urlsafe_b64decode(encrypted.encode())
        return self._private_key.decrypt(
            encrypted, *self._encryption_parameters()).decode()

    def sign(self, message):
        """
        Sign a message with private key.

        Args:
            message (str): Message to sign.

        Returns:
            str: signature.
        """
        signature = self._private_key.sign(
            message.encode(), *self._signature_parameters())
        return base64.urlsafe_b64encode(signature).decode()

    # Utilities

    @staticmethod
    def _encryption_parameters():
        """Parameters for encryption functions

        Returns:
            tuple: parameters"""
        return (padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(), label=None),)

    @staticmethod
    def _signature_parameters():
        """Parameters for signature functions

        Returns:
            tuple: parameters"""
        return (padding.PSS(mgf=padding.MGF1(hashes.SHA256()),
                            salt_length=padding.PSS.MAX_LENGTH),
                hashes.SHA256())


class SymmetricCipher:
    """Symmetric cipher for encryption.

    Args:
        key (str): Key in PEM format.
            If not specified, a new key will be generated.
    """

    def __init__(self, key=None):
        self._key = None

        # Generate new key if not exists
        if not key:
            self._key = Fernet.generate_key()

        # Load key
        else:
            self._key = key.encode()

        self._fernet = Fernet(self._key)

    @property
    def key(self):
        """Key

        Returns:
            str: Key.
        """
        return self._key.decode()

    def encrypt(self, message):
        """
        Encrypt with public key.

        Args:
            message (str): Message to encrypt

        Returns:
            str: encrypted message
        """
        return self._fernet.encrypt(message.encode()).decode()

    def decrypt(self, encrypted):
        """
        Decrypt message with private key.

        Args:
            encrypted (str): Encrypted message

        Returns:
            str: Decrypted message
        """
        try:
            return self._fernet.decrypt(encrypted.encode()).decode()
        except InvalidToken:
            raise ValueError('Unable to decrypt value')
