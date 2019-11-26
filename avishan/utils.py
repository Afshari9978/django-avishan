from typing import Optional

from django.http import HttpResponse

from avishan.exceptions import AuthException
from avishan.misc.bch_datetime import BchDatetime
from avishan.models.authentication import AuthenticationType
from avishan_config import AvishanConfig
from . import current_request


def discard_monitor(url: str) -> bool:
    """
    checks if request is in check-blacklist
    :param url: request url. If straightly catch from request.path, it comes like: /admin, /api/v1
    :return:
    """
    from avishan_config import AvishanConfig
    if url.startswith(AvishanConfig.NOT_MONITORED_STARTS):
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


def add_token_to_response(rendered_response: HttpResponse, delete_token: bool = False):
    """
    create new token if needed, else reuse previous
    add token to session if session-based auth, else to response header
    """
    if delete_token or not current_request['add_token']:
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


def encode_token(authentication_object: AuthenticationType) -> Optional[str]:
    import jwt
    from datetime import timedelta
    from avishan_config import AvishanConfig

    now = BchDatetime()
    token_data = {
        'at_n': authentication_object.class_name(),
        'at_id': authentication_object.id,
        'exp': (now + timedelta(
            seconds=authentication_object.user_user_group.user_group.token_valid_seconds)).to_unix_timestamp(),
        'crt': now.to_unix_timestamp(),
        'lgn': BchDatetime(authentication_object.last_login).to_unix_timestamp()
    }
    return jwt.encode(token_data,
                      AvishanConfig.JWT_KEY,
                      algorithm='HS256'
                      ).decode("utf8")


def decode_token():
    import jwt
    if not current_request['token']:
        raise AuthException(AuthException.TOKEN_NOT_FOUND)
    try:
        current_request['decoded_token'] = jwt.decode(
            current_request['token'], AvishanConfig.JWT_KEY,
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
        authentication_type_object: AuthenticationType = authentication_type_class.objects.get(
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


def populate_current_request(login_with: AuthenticationType):
    current_request['base_user'] = login_with.user_user_group.base_user
    current_request['user_group'] = login_with.user_user_group.user_group
    current_request['user_user_group'] = login_with.user_user_group
    current_request['authentication_object'] = login_with
    current_request['add_token'] = True


def create_avishan_config_file(app_name: str = None):
    if app_name:
        f = open(app_name + "/avishan_config.py", 'w+')
    else:
        f = open('avishan_config.py', 'w+')
    f.writelines((
        'def check():\n',
        '    pass\n\n\n',
        'class AvishanConfig:\n',
        '    pass\n'
    ))
    f.close()


def fa_numbers(text):
    text = str(text)
    text = en_number(text)
    array = ['۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹']
    result = ''
    for i in str(text):
        if i.isdigit():
            result = result + array[int(i)]
        else:
            result = result + i

    return result


def en_number(text):
    text = str(text)
    result = ''
    array = ['۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹']
    for char in text:
        if char in array:
            result += str(array.index(char))
        else:
            result += char
    return result
