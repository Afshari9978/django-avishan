from typing import Optional

from django.contrib import messages

from . import current_request
from .misc import status


class AvishanException(Exception):
    def __init__(
            self,
            wrap_exception: Optional[Exception] = None,
            status_code: int = status.HTTP_400_BAD_REQUEST
    ):
        save_traceback()
        if wrap_exception:
            if isinstance(wrap_exception, KeyError):
                body = f'field {wrap_exception.args[0]} not found in data and its required'
            else:
                body = str(wrap_exception.args[0]) if len(wrap_exception.args) == 1 else str(wrap_exception.args)
            current_request['exception'] = wrap_exception
            current_request['status_code'] = status.HTTP_418_IM_TEAPOT
            add_error_message_to_response(
                body=body,
            )
        else:
            current_request['exception'] = self
            current_request['status_code'] = status_code


class AuthException(AvishanException):
    from .misc.translation import translatable
    """
    Error kinds
    """
    NOT_DEFINED = 0, translatable(EN='Not Defined', FA='مشخص نشده')
    ACCOUNT_NOT_FOUND = 1, translatable(EN='User Account not found', FA='حساب کاربری پیدا نشد')
    ACCOUNT_NOT_ACTIVE = 2, translatable(EN='Deactivated User Account', FA='حساب کاربری غیرفعال است')
    GROUP_ACCOUNT_NOT_ACTIVE = 3, translatable(
        EN='User Account Deactivated in Selected User Group',
        FA='حساب کاربری در گروه‌کاربری انتخاب شده غیر فعال است'
    )
    TOKEN_NOT_FOUND = 4, translatable(EN='Token not found', FA='توکن پیدا نشد')
    TOKEN_EXPIRED = 5, translatable(EN='Token timed out', FA='زمان استفاده از توکن تمام شده است')
    ERROR_IN_TOKEN = 6, translatable(EN='Error in token', FA='خطا در توکن')
    ACCESS_DENIED = 7, translatable(EN='Access Denied', FA='دسترسی نامجاز')
    HTTP_METHOD_NOT_ALLOWED = 8, translatable(EN='HTTP method not allowed in this url')
    INCORRECT_PASSWORD = 9, translatable(EN='Incorrect Password', FA='رمز اشتباه است')
    DUPLICATE_AUTHENTICATION_IDENTIFIER = 10, translatable(
        EN='Authentication Identifier already Exists',
        FA='شناسه احراز هویت تکراری است'
    )
    DUPLICATE_AUTHENTICATION_TYPE = 11, translatable(
        EN='Duplicate Authentication Type for User Account',
        FA='روش احراز هویت برای این حساب کاربری تکراری است'
    )
    DEACTIVATED_TOKEN = 12, translatable(
        EN='Token Deactivated, Sign in again',
        FA='توکن غیرفعال شده است، دوباره وارد شوید'
    )
    MULTIPLE_CONNECTED_ACCOUNTS = 13, translatable(
        EN='Multiple Accounts found with this identifier, Choose user group in url parameter',
        FA='چند حساب با این شناسه پیدا شد، گروه کاربری را در پارامتر url مشخص کنید'
    )

    def __init__(self, error_kind: tuple = NOT_DEFINED):
        from .misc.translation import translatable
        status_code = status.HTTP_403_FORBIDDEN
        if error_kind[0] == AuthException.HTTP_METHOD_NOT_ALLOWED[0]:
            status_code = status.HTTP_405_METHOD_NOT_ALLOWED
        super().__init__(status_code=status_code)
        add_error_message_to_response(code=error_kind[0], body=error_kind[1], title=translatable(
            EN='Authentication Exception',
            FA='خطای احراز هویت'
        ))


class ErrorMessageException(AvishanException):
    def __init__(self, message: str = 'Error', status_code: int = status.HTTP_400_BAD_REQUEST):
        from .misc.translation import translatable
        super().__init__(status_code=status_code)
        add_error_message_to_response(
            body=message if message else translatable(
                EN='Error details not provided',
                FA='توضیحات خطا ارائه نشده'),
            title=translatable(
                EN='Error',
                FA='خطا'
            )
        )


def add_debug_message_to_response(body: str = None, title: str = None):
    debug = {}
    if body is not None:
        debug['body'] = body
    if title is not None:
        debug['title'] = title
    current_request['messages']['debug'].append(debug)


def add_info_message_to_response(body: str = None, title: str = None):
    info = {}
    if body is not None:
        info['body'] = body
    if title is not None:
        info['title'] = title
    current_request['messages']['info'].append(info)


def add_success_message_to_response(body: str = None, title: str = None):
    success = {}
    if body is not None:
        success['body'] = body
    if title is not None:
        success['title'] = title
    current_request['messages']['success'].append(success)


def add_warning_message_to_response(body: str = None, title: str = None):
    warning = {}
    if body is not None:
        warning['body'] = body
    if title is not None:
        warning['title'] = title
    current_request['messages']['warning'].append(warning)


def add_error_message_to_response(body: str = None, title: str = None, code=None):
    error = {}
    if body is not None:
        error['body'] = body
    if title is not None:
        error['title'] = title
    if code is not None:
        error['code'] = code
    current_request['messages']['error'].append(error)


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
        print(current_request['traceback'])
        if current_request['exception_record']:
            current_request['exception_record'].traceback = current_request['traceback']
            current_request['exception_record'].save()
