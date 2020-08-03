from typing import Optional, Union, List

from . import current_request
from .misc import status
from .misc.translation import AvishanTranslatable

"""
try:
    b = json.dumps(a, default=lambda o: o.__dict__, indent=2)
except Exception as e:
    c = 1
current_request['locals'] = json.dumps(exc_value.__traceback__.tb_frame.f_locals, default=lambda o: o.__dict__,
                                       indent=2)                                      
"""


# todo save locals too

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
                if len(wrap_exception.args) == 0:
                    body = wrap_exception.__class__.__name__
                elif len(wrap_exception.args) == 1:
                    body = str(wrap_exception.args[0])
                else:
                    body = str(wrap_exception.args)[1:-1]
            current_request['exception'] = wrap_exception
            current_request['status_code'] = status.HTTP_418_IM_TEAPOT
            add_error_message_to_response(
                body=body,
            )
        else:
            current_request['exception'] = self
            current_request['status_code'] = status_code


class AuthException(AvishanException):
    from .misc.translation import AvishanTranslatable
    """
    Error kinds
    """
    NOT_DEFINED = 0, AvishanTranslatable(EN='Not Defined', FA='مشخص نشده')
    ACCOUNT_NOT_FOUND = 1, AvishanTranslatable(EN='User Account not found', FA='حساب کاربری پیدا نشد')
    ACCOUNT_NOT_ACTIVE = 2, AvishanTranslatable(EN='Deactivated User Account', FA='حساب کاربری غیرفعال است')
    GROUP_ACCOUNT_NOT_ACTIVE = 3, AvishanTranslatable(
        EN='User Account Deactivated in Selected User Group',
        FA='حساب کاربری در گروه‌کاربری انتخاب شده غیر فعال است'
    )
    TOKEN_NOT_FOUND = 4, AvishanTranslatable(EN='Token not found', FA='توکن پیدا نشد')
    TOKEN_EXPIRED = 5, AvishanTranslatable(EN='Token timed out', FA='زمان استفاده از توکن تمام شده است')
    ERROR_IN_TOKEN = 6, AvishanTranslatable(EN='Error in token', FA='خطا در توکن')
    ACCESS_DENIED = 7, AvishanTranslatable(EN='Access Denied', FA='دسترسی غیرمجاز')
    HTTP_METHOD_NOT_ALLOWED = 8, AvishanTranslatable(EN='HTTP method not allowed in this url')
    INCORRECT_PASSWORD = 9, AvishanTranslatable(EN='Incorrect Password', FA='رمز اشتباه است')
    DUPLICATE_AUTHENTICATION_IDENTIFIER = 10, AvishanTranslatable(
        EN='Authentication Identifier already Exists',
        FA='شناسه احراز هویت تکراری است'
    )
    DUPLICATE_AUTHENTICATION_TYPE = 11, AvishanTranslatable(
        EN='Duplicate Authentication Type for User Account',
        FA='روش احراز هویت برای این حساب کاربری تکراری است'
    )
    DEACTIVATED_TOKEN = 12, AvishanTranslatable(
        EN='Token Deactivated, Sign in again',
        FA='توکن غیرفعال شده است، دوباره وارد شوید'
    )
    MULTIPLE_CONNECTED_ACCOUNTS = 13, AvishanTranslatable(
        EN='Multiple Accounts found with this identifier.',
        FA='چند حساب با این شناسه پیدا شد'
    )

    METHOD_NOT_DIRECT_CALLABLE = 14, AvishanTranslatable(
        EN='Method is not callable direct to model',
        FA='تابع به طور مستقیم قابل صدا زدن نیست'
    )

    PASSWORD_NOT_FOUND = 15, AvishanTranslatable(
        EN='Password not found for user account',
        FA='رمز برای این کاربری تنظیم نشده است'
    )

    def __init__(self, error_kind: tuple = NOT_DEFINED):
        from .misc.translation import AvishanTranslatable
        status_code = status.HTTP_403_FORBIDDEN
        self.error_kind = error_kind
        if error_kind[0] == AuthException.HTTP_METHOD_NOT_ALLOWED[0]:
            status_code = status.HTTP_405_METHOD_NOT_ALLOWED
        super().__init__(status_code=status_code)
        add_error_message_to_response(code=error_kind[0], body=str(error_kind[1]), title=str(AvishanTranslatable(
            EN='Authentication Exception',
            FA='خطای احراز هویت'
        )))

    @classmethod
    def get_login_required_errors(cls) -> List[tuple]:
        return [
            cls.ACCOUNT_NOT_FOUND,
            cls.ACCOUNT_NOT_ACTIVE,
            cls.GROUP_ACCOUNT_NOT_ACTIVE,
            cls.TOKEN_NOT_FOUND,
            cls.TOKEN_EXPIRED,
            cls.ERROR_IN_TOKEN,
            cls.INCORRECT_PASSWORD,
            cls.DEACTIVATED_TOKEN,
            cls.MULTIPLE_CONNECTED_ACCOUNTS
        ]


class ErrorMessageException(AvishanException):
    def __init__(self, message: Union[str, AvishanTranslatable] = 'Error',
                 status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code)
        message = str(message)
        # add_error_message_to_response(
        #     body=message if message else AvishanTranslatable(
        #         EN='Error details not provided',
        #         FA='توضیحات خطا ارائه نشده').__str__(),
        #     title=AvishanTranslatable(
        #         EN='Error',
        #         FA='خطا'
        #     ).__str__()
        # )
        add_error_message_to_response(
            body=message if message else 'Error details not provided',
            title='Error'
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
    if 'messages' not in current_request.keys():
        return
    error = {}
    if body is not None:
        error['body'] = body
    if title is not None:
        error['title'] = title
    if code is not None:
        error['code'] = code
    current_request['messages']['error'].append(error)


def save_traceback():
    try:
        if current_request['traceback'] is not None:
            return
    except KeyError:
        return
    import sys, traceback
    exc_type, exc_value, exc_tb = sys.exc_info()
    tbe = traceback.TracebackException(
        exc_type, exc_value, exc_tb,
    )
    if tbe.exc_traceback is not None:
        current_request['traceback'] = ''.join(tbe.format())
        if current_request['DEBUG']:
            print(current_request['traceback'])
        if current_request['exception_record']:
            current_request['exception_record'].traceback = current_request['traceback']
            current_request['exception_record'].save()
