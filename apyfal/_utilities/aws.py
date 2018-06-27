# coding=utf-8
"""AWS utilities"""

from contextlib import contextmanager

from botocore.exceptions import ClientError

from apyfal.exceptions import AcceleratorException


class ExceptionHandler:
    RUNTIME = AcceleratorException
    ERROR_CODE = dict()

    @classmethod
    @contextmanager
    def catch(cls, to_catch=ClientError, to_raise=None, filter_error_codes=None,
              exception_msg=None, **exc_kwargs):
        """
        Context manager that catch AWS exceptions and raises
        Apyfal exceptions.

        Args:
            to_catch (Exception or tuple of Exception): Exception to catch.
                ClientError if not specified.
            to_raise (apyfal.exception.AcceleratorException subclass):
                Exception to raise. self.RUNTIME if not specified.
            filter_error_codes (str or tuple of str):
                Don't raise exception if error code in this argument.
            exception_msg (str): Exception message.
            exc_kwargs: Exception to raise arguments.
        """
        # Performs operation
        try:
            yield

        # Catch specified exceptions
        except to_catch as exception:
            # Try to get error code and message
            try:
                error_dict = exception.response['Error']
                error_code = error_dict['Code']
            except (AttributeError, KeyError):
                raise cls.RUNTIME(
                    exception_msg, exc=exception)

            # Converts single str to tuple
            if filter_error_codes is None:
                filter_error_codes = ()
            elif isinstance(filter_error_codes, str):
                filter_error_codes = (filter_error_codes,)

            # Raises if not in filter
            if error_code not in filter_error_codes:
                exception = cls.ERROR_CODE.get(
                    error_code, to_raise or cls.RUNTIME)
                raise exception(
                    exception_msg, exc=error_dict['Message'], **exc_kwargs)
