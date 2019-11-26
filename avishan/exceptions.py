from typing import Optional

from django.contrib import messages

from . import current_request
from .misc import status, translatable


class AvishanException(Exception):
    def __init__(
            self,
            wrap_exception: Optional[Exception] = None,
            error_message: Optional[str] = None,
            status_code: int = status.HTTP_400_BAD_REQUEST
    ):
        save_traceback()
        # todo 0.2.4: record exception
        # todo 0.2.1: wrap exception
        if wrap_exception:
            add_error_to_response(
                body=str(wrap_exception.args),
            )
            current_request['exception'] = wrap_exception
            current_request['status_code'] = status.HTTP_500_INTERNAL_SERVER_ERROR
        else:
            add_error_to_response(
                body=error_message if error_message else translatable(EN='Error details not provided',
                                                                      FA='توضیحات خطا ارائه نشده'))
            current_request['exception'] = self
            current_request['status_code'] = status_code


class AuthException(AvishanException):
    """
    Error kinds
    """
    NOT_DEFINED = 0, translatable(EN='not defined', FA='مشخص نشده')
    ACCOUNT_NOT_FOUND = 1, translatable(EN='user account not found', FA='حساب کاربری پیدا نشد')
    ACCOUNT_NOT_ACTIVE = 2, translatable(EN='user account is deactive', FA='حساب کاربری غیرفعال است')
    GROUP_ACCOUNT_NOT_ACTIVE = 3, translatable(
        EN='user account deactivated in selected user group',
        FA='حساب کاربری در گروه‌کاربری انتخاب شده غیر فعال است'
    )
    TOKEN_NOT_FOUND = 4, translatable(EN='token not found', FA='توکن پیدا نشد')
    TOKEN_EXPIRED = 5, translatable(EN='token timed out', FA='زمان استفاده از توکن تمام شده است')
    ERROR_IN_TOKEN = 6, translatable(EN='error in token', FA='خطا در توکن')
    ACCESS_DENIED = 7, translatable(EN='Access Denied', FA='دسترسی نامجاز')
    HTTP_METHOD_NOT_ALLOWED = 8, translatable(EN='HTTP method not allowed in this url')
    INCORRECT_PASSWORD = 9, translatable(EN='incorrect password', FA='رمز اشتباه است')
    DUPLICATE_AUTHENTICATION_IDENTIFIER = 10, translatable(
        EN='authentication identifier already exists',
        FA='شناسه احراز هویت تکراری است'
    )
    DUPLICATE_AUTHENTICATION_TYPE = 11, translatable(
        EN='duplicate authentication type for user account',
        FA='روش احراز هویت برای این حساب کاربری تکراری است'
    )
    DEACTIVATED_TOKEN = 12, translatable(
        EN='token deactivated, sign in again',
        FA='توکن غیرفعال شده است، دوباره وارد شوید'
    )

    def __init__(self, error_kind: tuple = NOT_DEFINED):
        status_code = status.HTTP_403_FORBIDDEN
        if error_kind[0] == AuthException.HTTP_METHOD_NOT_ALLOWED[0]:
            status_code = status.HTTP_405_METHOD_NOT_ALLOWED
        super().__init__(error_message=error_kind[1], status_code=status_code)
        add_error_to_response(code=error_kind[0], body=error_kind[1], title=translatable(
            EN='Authentication Exception',
            FA='خطای احراز هویت'
        ))


class ErrorMessageException(AvishanException):
    def __init__(self, message: str = 'Error', status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(error_message=message, status_code=status_code)


def add_error_to_response(body: str = None, title: str = None, code=None):
    error = {}
    if body is not None:
        error['body'] = body
    if title is not None:
        error['title'] = title
    if code is not None:
        error['code'] = code
    current_request['errors'].append(error)
    messages.error(current_request['request'], body if body else title)


def add_warning_to_response(body: str = None, title: str = None):
    warning = {}
    if body is not None:
        warning['body'] = body
    if title is not None:
        warning['title'] = title
    current_request['warnings'].append(warning)
    messages.warning(current_request['request'], body if body else title)


def save_traceback():
    if current_request['traceback'] is not None:
        return
    import sys, traceback
    exc_type, exc_value, exc_tb = sys.exc_info()
    tbe = traceback.TracebackException(
        exc_type, exc_value, exc_tb,
    )
    if tbe.exc_traceback is not None:
        current_request['traceback'] = ''.join(tbe.format())


def raise_exception(exception: Exception):
    pass
