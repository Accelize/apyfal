# coding=utf-8
"""AcceleratorAPI Exceptions"""


class AcceleratorApiBaseException(Exception):
    """Base exception for acceleratorAPI exceptions

    Args:
        msg (str): Exception message
        exc: Exception or other details to add to description"""
    DEFAULT_MESSAGE = ""

    def __init__(self, msg=None,  exc=None, *args, **kwargs):
        # Set default message if nothing passed as argument.
        if not msg and self.DEFAULT_MESSAGE:
            msg = self.DEFAULT_MESSAGE

        if exc is not None:
            msg = '%s, more details: %r' % (msg.rstrip('.'), exc)
        Exception.__init__(self, msg, *args, **kwargs)


class AcceleratorException(AcceleratorApiBaseException):
    """Generic AcceleratorClient related exception."""


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


class CSPAuthenticationException(CSPException):
    """Error while trying to authenticate user on CSP."""
    DEFAULT_MESSAGE = "Failed to authenticate with your CSP access key."


class CSPConfigurationException(CSPException):
    """Error with CSP configuration"""
