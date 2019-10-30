from typing import Optional
from . import current_request
from avishan.utils import add_data_to_response
from .misc import status


class AvishanException(Exception):
    def __init__(
            self,
            wrap_exception: Optional[Exception] = None,
            error_message: Optional[str] = None,
            status_code: int = status.HTTP_400_BAD_REQUEST
    ):
        # todo record exception 0.2.4
        add_data_to_response('error_message', error_message if error_message else 'NOT_PROVIDED')
        current_request['status_code'] = status_code


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
    INVALID_TOKEN = 6
    ACCESS_DENIED = 7
    HTTP_METHOD_NOT_ALLOWED = 8
    INCORRECT_PASSWORD = 9
    DUPLICATE_AUTHENTICATION_IDENTIFIER = 10
    DUPLICATE_AUTHENTICATION_TYPE = 11

    def __init__(self, error_kind: int = NOT_DEFINED):
        add_data_to_response('error_kind', error_kind)
        status_code = status.HTTP_403_FORBIDDEN
        if error_kind == AuthException.HTTP_METHOD_NOT_ALLOWED:
            status_code = status.HTTP_405_METHOD_NOT_ALLOWED
        super().__init__(error_message=self.get_error_kind_text(error_kind), status_code=status_code)

    def get_error_kind_text(self, error_kind: int):
        return 'AuthException'  # todo: find error kind from class variables 0.2.2


class ErrorMessageException(AvishanException):
    def __init__(self, message: str = 'Error', status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(error_message=message, status_code=status_code)
