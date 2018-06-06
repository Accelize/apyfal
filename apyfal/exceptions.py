# coding=utf-8
"""Apyfal Exceptions"""

from apyfal._utilities import gen_msg as _get_msg


class AcceleratorException(Exception):
    """Base exception for apyfal exceptions

    Args:
        msg (str): Exception message
        gen_msg (tuple of str or str): Arguments for apyfal._utilities.gen_msg
        exc (Exception or str): Exception or other details to
            add to description"""
    DEFAULT_MESSAGE = ""

    def __init__(self, msg=None, gen_msg=None, exc=None, *args, **kwargs):
        # Gets message from pre-generated messages
        if gen_msg:
            if isinstance(gen_msg, str):
                gen_msg = (gen_msg,)
            msg = _get_msg(*gen_msg)

        # Sets default message if nothing passed as argument.
        msg = msg or self.DEFAULT_MESSAGE

        # Augments exception with source error message
        if exc is not None:
            msg = '%s: %r' % (msg.rstrip('.'), exc)
        Exception.__init__(self, msg, *args, **kwargs)


class ClientException(AcceleratorException):
    """Generic AcceleratorClient related exception."""
    DEFAULT_MESSAGE = "Accelerator Client Error"


class ClientAuthenticationException(ClientException):
    """Error while trying to authenticate user on Accelize server."""
    DEFAULT_MESSAGE = "Accelize authentication failed"


class ClientConfigurationException(ClientException):
    """Error with AcceleratorClient configuration."""


class ClientRuntimeException(ClientException):
    """Error with AcceleratorClient running."""


class HostException(AcceleratorException):
    """Generic host related exception"""


class HostRuntimeException(HostException):
    """Error with host on runtime"""
    DEFAULT_MESSAGE = "Host Exception"


class HostAuthenticationException(HostException):
    """Error while trying to authenticate user on host."""
    DEFAULT_MESSAGE = "Failed to authenticate to host."


class HostConfigurationException(HostException):
    """Error with host configuration"""
