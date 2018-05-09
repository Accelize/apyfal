# coding=utf-8
"""AcceleratorAPI Exceptions"""


class AcceleratorApiBaseException(Exception):
    """Base exception for acceleratorAPI exceptions"""
    DEFAULT_MESSAGE = ""

    def __init__(self, *args, **kwargs):
        # Set default message if nothing passed as argument.
        if not args and self.DEFAULT_MESSAGE:
            args = (self.DEFAULT_MESSAGE,)
        Exception.__init__(self, *args, **kwargs)


class AcceleratorException(AcceleratorApiBaseException):
    """Generic accelerator related exception."""


class AcceleratorAuthenticationException(AcceleratorException):
    """Error while trying to authenticate user on Accelize server."""


class AcceleratorConfigurationException(AcceleratorException):
    """Error with Accelerator configuration."""


class AcceleratorRuntimeException(AcceleratorException):
    """Error with Accelerator running."""


class CSPException(AcceleratorApiBaseException):
    """Generic CSP related exception"""


class CSPInstanceException(CSPException):
    """Error with CSP instance"""


class CSPAuthenticationException(CSPException):
    """Error while trying to authenticate user on CSP."""
    DEFAULT_MESSAGE = "Failed to authenticate with your CSP access key."


class CSPConfigurationException(CSPException):
    """Error with CSP configuration"""
