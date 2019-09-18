import sys

from .utils.bch_datetime import BchDatetime
from .utils.data_functions import save_traceback
from .utils import status
import traceback
from avishan_wrapper import current_request


class AvishanException(Exception):
    def __init__(self, from_exception: Exception = None):
        self.user = current_request['user']
        self.user_group = current_request['user_group']
        self.request_url = current_request['request'].path
        self.request_method = current_request['request'].method
        self.request_headers = None

        for key, value in current_request['request'].META.items():
            if key.startswith('HTTP_'):
                if not self.request_headers:
                    self.request_headers = ""
                self.request_headers += f'({key[5:]}: {value}),\n'

        try:
            self.request_data = current_request['request'].data if (
                    self.request_method != 'GET' or self.request_method != 'DELETE') else {}
        except AttributeError:
            self.request_data = {}

        if not current_request['traceback']:
            save_traceback()
        self.traceback = current_request['traceback']

        self.response = current_request['response']
        if not from_exception:
            self.status_code = current_request['status_code']
            self.class_title = self.__class__.__name__
            self.exception_args = None

        else:
            self.class_title = from_exception.__class__.__name__
            self.status_code = current_request['status_code'] = status.HTTP_500_INTERNAL_SERVER_ERROR
            self.exception_args = str(from_exception.args)

            current_request['response'] = {
                'error_message': 'خطای سرور'
            }

        from .models import ExceptionRecord
        ExceptionRecord.objects.create(
            class_title=self.class_title,
            user=self.user,
            user_group=self.user_group,
            status_code=self.status_code,
            request_url=self.request_url,
            request_method=self.request_method,
            request_data=self.request_data,
            request_headers=self.request_headers,
            response=self.response,
            traceback=self.traceback,
            exception_args=self.exception_args,
        )


class AuthException(AvishanException):
    ACCOUNT_NOT_FOUND = 0
    ACCOUNT_NOT_ACTIVE = 1
    TOKEN_EXPIRED = 2
    WTF = 3
    ADMIN_PERMISSION_NEEDED = 4
    INCORRECT_PASSWORD = 5
    UNAUTHORIZED_ROLE = 6
    INCORRECT_SMS_CODE = 7
    SMS_CODE_EXPIRED = 8
    INCORRECT_TOKEN = 9
    TOKEN_ERROR = 10
    ACCESS_DENIED = 11

    def __init__(self, error_type):
        current_request['response']['error_type'] = error_type
        current_request['status_code'] = status.HTTP_403_FORBIDDEN
        self.error_type = error_type

        if error_type == 0:
            error_message = 'ACCOUNT_NOT_FOUND'
        elif error_type == 1:
            error_message = 'ACCOUNT_NOT_ACTIVE'
        elif error_type == 2:
            error_message = 'TOKEN_EXPIRED'
        elif error_type == 4:
            error_message = 'ADMIN_PERMISSION_NEEDED'
        elif error_type == 5:
            error_message = 'INCORRECT_PASSWORD'
        elif error_type == 6:
            error_message = 'UNAUTHORIZED_ROLE'
        elif error_type == 7:
            error_message = 'INCORRECT_SMS_CODE'
        elif error_type == 8:
            error_message = 'SMS_CODE_EXPIRED'
        elif error_type == 9:
            error_message = 'INCORRECT_TOKEN'
        elif error_type == 10:
            error_message = 'TOKEN_ERROR'
            current_request['status_code'] = status.HTTP_424_FAILED_DEPENDENCY
        elif error_type == 11:
            error_message = 'ACCESS_DENIED'
        # todo: in che margiye
        else:
            error_message = 'WTF'

        current_request['response']['error_message'] = error_message
        super().__init__()


class ErrorMessageException(AvishanException):

    def __init__(self, message: str = None, status_code: int = status.HTTP_400_BAD_REQUEST):

        if not message:
            message = 'خطا'
        current_request['response']['error_message'] = message
        current_request['status_code'] = status_code
        super().__init__()


class ValidatorException(AvishanException):

    def __init__(self, field_name: str):
        current_request['response']['error_in_field'] = field_name
        current_request['response']['error_message'] = '"' + field_name + '" قابل قبول نیست'
        current_request['status_code'] = status.HTTP_417_EXPECTATION_FAILED
        super().__init__()


def add_warning_message(text: str):
    current_request['response']['warning_message'] = text
