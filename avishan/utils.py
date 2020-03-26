import datetime
from typing import Optional, Union, List

from django.http import HttpResponse

from avishan.exceptions import AuthException, AvishanException
from avishan.misc.bch_datetime import BchDatetime
from . import current_request
from .configure import get_avishan_config
from .misc import status
from .models import AuthenticationType


class AvishanDataValidator:
    class ValidatorException(AvishanException):
        from avishan.misc.translation import AvishanTranslatable

        def __init__(self, field_name: Union[str, 'AvishanTranslatable']):
            from avishan.misc.translation import AvishanTranslatable
            current_request['response']['error_in_field'] = field_name
            current_request['response']['error_message'] = AvishanTranslatable(
                EN=f'"{field_name}" not accepted',
                FA='"' + field_name + '" قابل قبول نیست'
            )
            current_request['status_code'] = status.HTTP_417_EXPECTATION_FAILED
            super().__init__()

    @classmethod
    def validate_phone_number(cls, input: str, country_code: str = '98', phone_start_number: str = '09') -> str:
        from avishan.misc.translation import AvishanTranslatable

        input = en_numbers(input)
        input = input.replace(" ", "")
        input = input.replace("-", "")

        if input.startswith("00"):
            if not input.startswith("00" + country_code):
                raise cls.ValidatorException(AvishanTranslatable(
                    EN='phone number', FA='شماره موبایل'
                ))
            if input.startswith("00" + country_code + phone_start_number):
                input = "00" + country_code + input[5:]
        elif input.startswith("+"):
            if not input.startswith("+" + country_code):
                raise cls.ValidatorException(AvishanTranslatable(
                    EN='phone number', FA='شماره موبایل'
                ))
            input = "00" + input[1:]
            if input.startswith("00" + country_code + phone_start_number):
                input = "00" + country_code + input[5:]
        elif input.startswith(phone_start_number):
            input = "00" + country_code + input[1:]

        if len(input) != 14 or not input.isdigit():
            raise cls.ValidatorException(AvishanTranslatable(
                EN='phone number', FA='شماره موبایل'
            ))

        return input

    @classmethod
    def validate_text(cls, input: str, blank: bool = True) -> str:
        input = input.strip()
        input = fa_numbers(input)

        if not blank and len(input) == 0:
            from avishan.misc.translation import AvishanTranslatable
            raise cls.ValidatorException(AvishanTranslatable(EN='text', FA='متن'))

        return input

    @classmethod
    def validate_recommend_code(cls, input: str) -> str:
        input = cls.validate_text(input)

        input = en_numbers(input)

        input = input.upper()

        return input

    @classmethod
    def validate_first_name(cls, input):
        input = input.strip()

        if has_numbers(input) or len(input) < 2:
            from avishan.misc.translation import AvishanTranslatable
            raise cls.ValidatorException(AvishanTranslatable(EN='first name', FA='نام'))

        return input

    @classmethod
    def validate_last_name(cls, input):
        input = input.strip()

        if has_numbers(input) or len(input) < 2:
            from avishan.misc.translation import AvishanTranslatable
            raise cls.ValidatorException(AvishanTranslatable(EN='last name', FA='نام خانوادگی'))

        return input

    @classmethod
    def validate_ferdowsi_student_id(cls, input):
        input = cls.validate_text(input, blank=False)

        if not input.isdigit():
            from avishan.misc.translation import AvishanTranslatable
            raise cls.ValidatorException(AvishanTranslatable(EN='Student ID', FA='کد دانشجویی'))
        return input

    @classmethod
    def validate_plate(cls, plate_a, plate_b, plate_c, plate_d):
        from avishan.misc.translation import AvishanTranslatable
        plate_a = cls.validate_text(fa_numbers(plate_a), blank=False)
        plate_b = cls.validate_text(fa_numbers(plate_b), blank=False)
        plate_c = cls.validate_text(fa_numbers(plate_c), blank=False)
        plate_d = cls.validate_text(fa_numbers(plate_d), blank=False)

        if plate_b not in ['ب', 'ج', 'د', 'س', 'ص', 'ط', 'ق', 'ل', 'م', 'ن', 'و', 'ه', 'ی', 'الف', 'پ', 'ت', 'ث', 'ز',
                           'ژ',
                           'ش', 'ع', 'ف', 'ک', 'گ', 'D', 'S', 'd', 's', 'ي']:
            raise cls.ValidatorException(AvishanTranslatable(EN='plate', FA='پلاک'))

        if not plate_a.isdigit() or not plate_c.isdigit() or not plate_d.isdigit():
            raise cls.ValidatorException(AvishanTranslatable(EN='plate', FA='پلاک'))

        return plate_a, plate_b, plate_c, plate_d

    @classmethod
    def validate_time(cls, input: dict, name: str) -> datetime.time:
        return datetime.time(int(input['hour']), int(input['minute']))


def discard_monitor(url: str) -> bool:
    """
    checks if request is in check-blacklist
    :param url: request url. If straightly catch from request.path, it comes like: /admin, /api/v1
    :return:
    """
    if url.startswith(tuple(get_avishan_config().NOT_MONITORED_STARTS)):
        return True
    return False


def find_token_in_header() -> bool:
    """
    find token and put it in current_request
    :return: false if token not found
    """
    try:
        temp = current_request['request'].META['HTTP_AUTHORIZATION']
        if can_be_token(temp[6:]):
            current_request['token'] = temp[6:]
            return True
    except KeyError:
        pass

    return False


def find_token_in_session() -> bool:
    """
    find token and put it in current_request
    :return: false if token not found
    """
    try:
        temp = current_request['request'].COOKIES['token']
        if can_be_token(temp):
            current_request['token'] = temp
            return True
    except KeyError:
        pass

    return False


def find_token() -> bool:
    """
    check for token in both session and header
    :return: true if token
    """
    if current_request['request'].path.startswith('/api/v1/login/generate/'):
        return False
    if not find_token_in_header() and not find_token_in_session():
        return False
    return True


def can_be_token(text):
    """
    checks entered text can be a token
    :param text:
    :return:
    """
    # todo 0.2.2: can we use jwt package itself for check?
    if len(text) > 0:
        return True
    return False


def add_token_to_response(rendered_response: HttpResponse):
    """
    create new token if needed, else reuse previous
    add token to session if session-based auth, else to response header
    """
    if current_request['json_unsafe']:
        return
    if not current_request['add_token']:
        delete_token_from_request(rendered_response)

    if not current_request['authentication_object']:
        delete_token_from_request(rendered_response)
    else:
        token = encode_token(current_request['authentication_object'])

        if current_request['is_api']:
            # todo 0.2.0: where should be?
            current_request['response']['token'] = token

        else:
            rendered_response.set_cookie('token', token)


def delete_token_from_request(rendered_response=None):
    if current_request['is_api']:
        try:
            del current_request['response']['token']
        except KeyError:
            pass
    else:
        rendered_response.delete_cookie('token')


def encode_token(authentication_object: 'AuthenticationType') -> Optional[str]:
    import jwt
    from datetime import timedelta

    now = BchDatetime()
    token_data = {
        'at_n': authentication_object.class_name(),
        'at_id': authentication_object.id,
        'exp': (now + timedelta(
            seconds=authentication_object.user_user_group.user_group.token_valid_seconds)).to_unix_timestamp(),
        'crt': now.to_unix_timestamp(),
        'lgn':
            BchDatetime(authentication_object.last_login).to_unix_timestamp()
            if authentication_object.last_login
            else now.to_unix_timestamp()
    }
    return jwt.encode(token_data,
                      get_avishan_config().JWT_KEY,
                      algorithm='HS256'
                      ).decode("utf8")


def decode_token():
    import jwt
    if not current_request['token']:
        raise AuthException(AuthException.TOKEN_NOT_FOUND)
    try:
        current_request['decoded_token'] = jwt.decode(
            current_request['token'], get_avishan_config().JWT_KEY,
            algorithms=['HS256']
        )
        current_request['add_token'] = True
    except jwt.exceptions.ExpiredSignatureError:
        raise AuthException(AuthException.TOKEN_EXPIRED)
    except:
        raise AuthException(AuthException.ERROR_IN_TOKEN)


def find_and_check_user():
    """
    Populate current_request object with data from token. Then check for user "active" authorization
    :return:
    """
    from avishan.models import AvishanModel

    if not current_request['decoded_token']:
        AuthException(AuthException.ERROR_IN_TOKEN)

    authentication_type_class = AvishanModel.get_model_with_class_name(
        current_request['decoded_token']['at_n']
    )
    try:
        authentication_type_object: 'AuthenticationType' = authentication_type_class.objects.get(
            id=current_request['decoded_token']['at_id'])
        user_user_group = authentication_type_object.user_user_group
    except authentication_type_class.DoesNotExist:
        raise AuthException(AuthException.ACCOUNT_NOT_FOUND)

    if not user_user_group.is_active:
        raise AuthException(AuthException.GROUP_ACCOUNT_NOT_ACTIVE)
    if not user_user_group.base_user.is_active:
        raise AuthException(AuthException.ACCOUNT_NOT_ACTIVE)
    if BchDatetime(authentication_type_object.last_login).to_unix_timestamp() != current_request['decoded_token'][
        'lgn'] or authentication_type_object.last_logout:
        raise AuthException(AuthException.DEACTIVATED_TOKEN)

    populate_current_request(login_with=authentication_type_object)


def populate_current_request(login_with: 'AuthenticationType'):
    current_request['base_user'] = login_with.user_user_group.base_user
    current_request['user_group'] = login_with.user_user_group.user_group
    current_request['user_user_group'] = login_with.user_user_group
    current_request['authentication_object'] = login_with
    if current_request['language'] is None:
        current_request['language'] = login_with.user_user_group.base_user.language
    current_request['add_token'] = True


def create_avishan_config_file(app_name: str = None):
    # todo 0.2.0 create config file and its classes. add needed fields
    """
    MONITORED_APPS_NAMES = []
    NOT_MONITORED_STARTS [
        '/admin', '/static', '/media', '/favicon.ico'
    ]
    JWT_KEY = "" or none if not available
    """
    if app_name:
        f = open(app_name + "/avishan_config.py", 'w+')
    else:
        f = open('avishan_config.py', 'w+')
    f.writelines((
        'def check():\n',
        '    pass\n\n\n',
        'class AvishanConfig:\n'
    ))
    if not app_name:
        f.writelines([
            '    MONITORED_APPS_NAMES = []\n',
            "    NOT_MONITORED_STARTS = ['/admin', '/static', '/favicon.ico']\n",
            "    JWT_KEY = 'CHANGE_THIS_KEY'\n",
            "    USE_JALALI_DATETIME = True\n",
        ])
    else:
        f.write("    pass\n")
    f.close()


def fa_numbers(text):
    text = str(text)
    text = en_numbers(text)
    array = ['۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹']
    result = ''
    for i in str(text):
        if i.isdigit():
            result = result + array[int(i)]
        else:
            result = result + i

    return result


def en_numbers(text):
    text = str(text)
    result = ''
    array = ['۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹']
    for char in text:
        if char in array:
            result += str(array.index(char))
        else:
            result += char
    return result


def has_numbers(input):
    return any(char.isdigit() for char in input)


def find_file(name: str, parent_directory_path: str) -> List[str]:
    import os

    result = []
    for root, dirs, files in os.walk(parent_directory_path):
        if name in files:
            result.append(os.path.join(root, name))
    return result


def all_subclasses(parent_class):
    return list(set(parent_class.__subclasses__()).union(
        [s for c in parent_class.__subclasses__() for s in all_subclasses(c)]))


def parse_url(url: str):
    from urllib.parse import urlparse
    return urlparse(url)
