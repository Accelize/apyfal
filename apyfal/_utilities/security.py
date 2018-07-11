# coding=utf-8
"""Generic security utilities"""
import base64

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature

from apyfal.exceptions import ClientSecurityException


class AsymmetricCipher:
    """Asymmetric cipher for encryption and signature.

    Args:
        public_key (str): Public key in PEM format.
            If not specified, a new key pair will be generated.
        private_key (str): Private key in PEM format.
    """

    def __init__(self, public_key=None, private_key=None):
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

            # Load private key
            if private_key:
                self._private_key = serialization.load_pem_private_key(
                    private_key.encode(), backend=default_backend(),
                    password=None)

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
        """
        signature = base64.urlsafe_b64decode(signature.encode())
        try:
            self._public_key.verify(
                signature, message.encode(),
                *self._signature_parameters())
        except InvalidSignature:
            raise ClientSecurityException('Invalid Signature')

    # Private key only functions

    @property
    def private_key(self):
        """Private key

        Returns:
            str: Private key in PEM format.
        """
        return self._private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode()

    def decrypt(self, encrypted):
        """
        Decrypt message with private key.

        Args:
            encrypted (str): Encrypted message

        Returns:
            str: Decrypted message
        """
        encrypted = base64.urlsafe_b64decode(encrypted.encode())
        try:
            return self._private_key.decrypt(
                encrypted, *self._encryption_parameters()).decode()
        except ValueError:
            raise ClientSecurityException('Decryption Error')

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
            raise ClientSecurityException('Decryption Error')


class CryptoServer:
    """
    Manage cryptography server side.

    Args:
        config (apyfal.configuration.Configuration):
            Configuration.
    """

    def __init__(self, config):

        # Configuration
        self._use_signature = (
            config['security']['use_signature'] or True)
        self._use_encryption = (
            config['security']['use_encryption'] or True)

        # Server asymmetric cipher
        self._asym_cipher = AsymmetricCipher()

        # Client authorized public keys
        self._client_public_keys = set()

        # Opened sessions with client
        # Contains: (AsymmetricCipher, SymmetricCipher)
        self._client_sessions = {}

    def authorize_public_keys(self, *public_keys):
        """Register public keys

        Args:
            public_keys (str):
        """
        self._client_public_keys.update(*public_keys)

    def revoke_public_keys(self, *public_keys):
        """Revoke public keys

        Args:
            public_keys (str):
        """
        self._client_public_keys.difference_update(*public_keys)

    def register_session(self, session, public_key):
        """
        Register a client session.

        Args:
            session (str): Session UUID
            public_key (str): Client public key.

        Returns:
            str: Symmetric key
        """
        if public_key not in self._client_public_keys:
            raise ClientSecurityException('Unknown public key')

        sym_cipher = SymmetricCipher()
        self._client_sessions[session] = (
            AsymmetricCipher(public_key=public_key), sym_cipher)

        return sym_cipher.key

    def unregister_session(self, session):
        """
        Unregister a client session.

        Args:
            session (str): Session UUID
        """
        del self._client_sessions[session]

    def encrypt(self, message, session):
        """
        Encrypt and sign data.

        Args:
            message (str): Message to write.
            session (str): Client session UUID

        Returns:
            Output message.
        """
        _, sym_cipher = self._client_sessions[session]

        # Encrypt data
        if self._use_encryption:
            message = sym_cipher.encrypt(message)

        # Sign data
        if self._use_signature:
            message = '%s:%s' % (
                message, self._asym_cipher.sign(message))

        return message

    def decrypt(self, message, session):
        """
        Verify signature and decrypt data.

        Args:
            message (str): Message to read.
            session (str): Client session UUID

        Returns:
            Output message.
        """
        try:
            asym_cipher, sym_cipher = self._client_sessions[session]
        except KeyError:
            raise ClientSecurityException('Invalid Session')

        # Verify signature
        if self._use_signature:
            signature, message = message.split(':')
            asym_cipher.verify(signature, message)

        # Decrypt data
        if self._use_encryption:
            message = sym_cipher.decrypt(message)

        return message


class CryptoClient:
    """Manage cryptography client side."""

    def __init(self, use_encryption, use_signature,
               private_key, public_key, sym_key,
               host_public_key):

        # Client side ciphers
        self._asym_cipher = AsymmetricCipher(
            public_key=public_key, private_key=private_key)
        self._sym_cipher = SymmetricCipher(
            key=sym_key)

        # Host side ciphers
        self._host_cipher = AsymmetricCipher(
            public_key=host_public_key)

        # Configuration
        self._use_encryption = use_encryption
        self._use_signature = use_signature

    def encrypt(self, message):
        """
        Encrypt and sign data.

        Args:
            message (str): Message to write.

        Returns:
            Output message.
        """
        # Encrypt data
        if self._use_encryption:
            message = self._sym_cipher.encrypt(message)

        # Sign data
        if self._use_signature:
            message = '%s:%s' % (
                message, self._asym_cipher.sign(message))

        return message

    def decrypt(self, message):
        """
        Verify signature and decrypt data.

        Args:
            message (str): Message to read.

        Returns:
            Output message.
        """
        # Verify signature
        if self._use_signature:
            signature, message = message.split(':')
            self._host_cipher.verify(signature, message)

        # Decrypt data
        if self._use_encryption:
            message = self._sym_cipher.decrypt(message)

        return message