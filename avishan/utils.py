from typing import Type

from avishan.exceptions import AvishanException, AuthException
from . import current_request


def must_monitor(url: str) -> bool:
    """
    checks if request is in check-blacklist
    :param url: request url
    :return:
    """
    # todo
    return True


def find_token_in_header() -> bool:
    """
    find token and put it in current_request
    :return: false if token not found
    """
    try:
        current_request['token'] = current_request['request'].META['HTTP_TOKEN']
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
        current_request['token'] = current_request['request'].COOKIES['TOKEN']
        if len(current_request['token']) > 0:
            return True
    except KeyError:
        pass

    return False


def find_token() -> bool:
    """
    check for token in both session and header
    :return: true if token
    """
    if not find_token_in_header():
        if not find_token_in_session():
            current_request['token'] = None
            current_request['is_api'] = None
            return False
        current_request['is_api'] = False
    else:
        current_request['is_api'] = True
    return True


def add_token_to_response():
    """
    create new token if needed, else reuse previous
    add token to session if session-based auth, else to response header
    """
    pass  # todo


def save_traceback_and_raise_exception(exception: AvishanException):
    # todo: save traceback
    # todo: save exception to current_request
    raise exception


def decode_token():
    import jwt
    token = current_request['token']
    if not token:
        raise AuthException(AuthException.TOKEN_NOT_FOUND)
    try:
        from avishan_config import JWT_KEY
        current_request['decoded_token'] = jwt.decode(token, JWT_KEY, algorithms=['HS256'])
    except jwt.exceptions.ExpiredSignatureError:
        AuthException(AuthException.TOKEN_EXPIRED)
    except:
        AuthException(AuthException.INVALID_TOKEN)


def find_and_check_user():
    from avishan.models.authentication import UserUserGroup
    if not current_request['decoded_token']:
        AuthException(AuthException.INVALID_TOKEN)
    try:

        user_user_group = UserUserGroup.objects.get(id=current_request['decoded_token']['uug_id'])
    except UserUserGroup.DoesNotExist:
        raise AuthException(AuthException.ACCOUNT_NOT_FOUND)
    if not user_user_group.is_active:
        raise AuthException(AuthException.GROUP_ACCOUNT_NOT_ACTIVE)
    if not user_user_group.base_user.is_active:
        raise AuthException(AuthException.ACCOUNT_NOT_ACTIVE)
    current_request['base_user'] = user_user_group.base_user
    current_request['user_group'] = user_user_group.user_group
    current_request['user_user_group'] = user_user_group
