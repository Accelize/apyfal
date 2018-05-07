# coding=utf-8
"""AcceleratorAPI Exceptions"""


class AcceleratorApiBaseException(Exception):
    """Base exception for acceleratorAPI exceptions"""


class AcceleratorException(AcceleratorApiBaseException):
    """Generic accelerator related exception."""


class AcceleratorAuthenticationException(AcceleratorException):
    """Error while trying to authenticate user."""


class AcceleratorConfigurationException(AcceleratorException):
    """Error with Accelerator configuration."""


class AcceleratorRuntimeException(AcceleratorException):
    """Error with Accelerator running."""


class CSPException(AcceleratorApiBaseException):
    """Generic CSP related exception"""


class CSPInstanceException(CSPException):
    """Error with CSP instance"""


class CSPAuthenticationException(CSPException):
    """Error while trying to authenticate user."""


class CSPConfigurationException(CSPException):
    """Error with CSP configuration"""
