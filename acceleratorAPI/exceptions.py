# coding=utf-8
"""AcceleratorAPI Exceptions"""

from acceleratorAPI._utilities import gen_msg as _get_msg


class AcceleratorApiBaseException(Exception):
    """Base exception for acceleratorAPI exceptions

    Args:
        msg (str): Exception message
        gen_msg (tuple of str or str): Arguments for acceleratorAPI._utilities.gen_msg
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


class AcceleratorException(AcceleratorApiBaseException):
    """Generic AcceleratorClient related exception."""
    DEFAULT_MESSAGE = "Accelerator Client Error"


class AcceleratorAuthenticationException(AcceleratorException):
    """Error while trying to authenticate user on Accelize server."""


class AcceleratorConfigurationException(AcceleratorException):
    """Error with AcceleratorClient configuration."""


class AcceleratorRuntimeException(AcceleratorException):
    """Error with AcceleratorClient running."""


class CSPException(AcceleratorApiBaseException):
    """Generic CSP related exception"""


class CSPInstanceException(CSPException):
    """Error with CSP instance"""
    DEFAULT_MESSAGE = "CSP Exception"


class CSPAuthenticationException(CSPException):
    """Error while trying to authenticate user on CSP."""
    DEFAULT_MESSAGE = "Failed to authenticate with your CSP access key."


class CSPConfigurationException(CSPException):
    """Error with CSP configuration"""
