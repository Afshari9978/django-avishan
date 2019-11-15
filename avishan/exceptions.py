from typing import Optional
from . import current_request
from .misc import status


class AvishanException(Exception):
    def __init__(
            self,
            wrap_exception: Optional[Exception] = None,
            error_message: Optional[str] = None,
            status_code: int = status.HTTP_400_BAD_REQUEST
    ):
        # todo 0.2.4: record exception
        # todo 0.2.1: wrap exception
        add_error_to_response(
            body=error_message if error_message else 'NOT_PROVIDED',
            status_code=status_code
        )
        current_request['exception'] = self


class AuthException(AvishanException):
    """
    Error kinds
    """
    NOT_DEFINED = 0
    ACCOUNT_NOT_FOUND = 1
    ACCOUNT_NOT_ACTIVE = 2
    GROUP_ACCOUNT_NOT_ACTIVE = 3
    TOKEN_NOT_FOUND = 4
    TOKEN_EXPIRED = 5
    ERROR_IN_TOKEN = 6
    ACCESS_DENIED = 7
    HTTP_METHOD_NOT_ALLOWED = 8
    INCORRECT_PASSWORD = 9
    DUPLICATE_AUTHENTICATION_IDENTIFIER = 10
    DUPLICATE_AUTHENTICATION_TYPE = 11
    DEPRECATED_TOKEN = 12
    INAPPROPRIATE_PROTOCOL = 13

    def __init__(self, error_kind: int = NOT_DEFINED):
        status_code = status.HTTP_403_FORBIDDEN
        if error_kind == AuthException.HTTP_METHOD_NOT_ALLOWED:
            status_code = status.HTTP_405_METHOD_NOT_ALLOWED
        super().__init__(error_message=self.get_error_kind_text(error_kind), status_code=status_code)
        add_error_to_response(code=error_kind, title='Authentication Exception')

    def get_error_kind_text(self, error_kind: int):
        return 'AuthException'  # todo: find error kind from class variables 0.2.2


class ErrorMessageException(AvishanException):
    def __init__(self, message: str = 'Error', status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(error_message=message, status_code=status_code)


def add_error_to_response(body: str = None, title: str = None, code=None, status_code: int = None):
    if current_request['error'] is None:
        current_request['error'] = {}
    if body is not None:
        current_request['error']['body'] = body
    if title is not None:
        current_request['error']['title'] = title
    if code is not None:
        current_request['error']['code'] = code
    if status_code is not None:
        current_request['error']['status_code'] = status_code


def add_warning_to_response(body: str = None, title: str = None):
    if current_request['warning'] is None:
        current_request['warning'] = {}
    if body is not None:
        current_request['warning']['body'] = body
    if title is not None:
        current_request['warning']['title'] = title
