# coding=utf-8
"""SSL Certificate management"""
from datetime import datetime, timedelta
from ipaddress import ip_address, AddressValueError, NetmaskValueError
from sys import version_info

from cryptography.x509 import (
    Name, NameAttribute, DNSName, IPAddress, SubjectAlternativeName,
    BasicConstraints, CertificateBuilder, random_serial_number,
    load_pem_x509_certificate)
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives.asymmetric.rsa import generate_private_key
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import (
    Encoding, PrivateFormat, NoEncryption)

#: Number of days of validity period
VALIDITY = 825


def self_signed_certificate(*hostname, **oid):
    """
    Generates a self signed ssl_cert_key.

    Args:
        hostname (str): host name or IP address.
        oid (str): Object Identifiers. See "cryptography.x509.oid.NameOID"

    Returns:
        tuple of bytes: certificate and private key in PEM format.
    """
    # Python 2: Unicode are required
    if version_info[0] == 2:
        oid = {key: unicode(value) for key, value in oid.items()}
        hostname = [unicode(value) for value in hostname]

    # Requester information
    name = Name([NameAttribute(
        getattr(NameOID, key.upper()), value) for key, value in oid.items()])

    # IP addresses
    alternatives_names = []
    for host in hostname:
        # DNS host name
        alternatives_names.append(DNSName(host))
        # Host IP address
        try:
            alternatives_names.append(IPAddress(ip_address(host)))
        except ValueError:
            pass

    # Validity start date
    valid_from = datetime.utcnow()

    # Generates private RSA key
    private_key = generate_private_key(
        public_exponent=65537, key_size=2048, backend=default_backend())

    # Generates ssl_cert_key
    certificate = (
        CertificateBuilder()
        # Requester information
        # Subject = Issuer on self signed certificates
        .subject_name(name)
        .issuer_name(name)

        # Public key and serial number
        .public_key(private_key.public_key())
        .serial_number(random_serial_number())

        # Validity
        .not_valid_before(valid_from)
        .not_valid_after(valid_from + timedelta(days=VALIDITY))

        # This ssl_cert_key can only sign itself
        .add_extension(
            BasicConstraints(ca=True, path_length=0), critical=False)

        # IP addresses
        .add_extension(
            SubjectAlternativeName(alternatives_names), critical=False)

        # Sign ssl_cert_key with private key
        .sign(private_key, SHA256(), default_backend()))

    # Generates public ssl_cert_key file
    certificate_bytes = certificate.public_bytes(encoding=Encoding.PEM)

    # Generates private key file
    private_key_bytes = private_key.private_bytes(
        encoding=Encoding.PEM, format=PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=NoEncryption())

    return certificate_bytes, private_key_bytes


def get_host_names_from_certificate(certificate_bytes):
    """
    Get host names from certificate.
    
    Args:
        certificate_bytes (bytes): Certificate in PEM format

    Returns:
        list of str: Host names
    """
    return (load_pem_x509_certificate(certificate_bytes, default_backend()).
            extensions.get_extension_for_class(SubjectAlternativeName).
            value.get_values_for_type(DNSName))
