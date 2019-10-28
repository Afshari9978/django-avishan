from django.http import HttpResponse

from avishan.exceptions import AvishanException, AuthException
from avishan.models.authentication import UserUserGroup, AuthenticationType
from . import current_request


def must_monitor(url: str) -> bool:
    """
    checks if request is in check-blacklist
    :param url: request url. If straightly catch from request.path, it comes like: /admin, /api/v1
    :return:
    """
    from bpm_dev.avishan_config import AvishanConfig
    if url.startswith(AvishanConfig.NOT_MONITORED_STARTS):
        return False
    # todo 0.2.0

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
        current_request['token'] = current_request['request'].COOKIES['token']
        if len(current_request['token']) > 0:
            print(current_request['token'])
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


def add_token_to_response(rendered_response: HttpResponse):
    """
    create new token if needed, else reuse previous
    add token to session if session-based auth, else to response header
    """
    token = encode_token(current_request['authentication_object'])

    if current_request['is_api']:
        current_request['response']['token'] = token

    else:
        rendered_response.set_cookie('token', token)


def encode_token(authentication_object: AuthenticationType) -> str:
    import jwt
    from avishan.misc.bch_datetime import BchDatetime
    from datetime import timedelta
    from bpm_dev.avishan_config import AvishanConfig

    now = BchDatetime()
    token_data = {
        'at_n': authentication_object.class_name(),
        'at_id': authentication_object.id,
        'exp': (now + timedelta(
            seconds=authentication_object.user_user_group.user_group.token_valid_seconds)).to_unix_timestamp(),
        'crt': now.to_unix_timestamp()
    }
    return jwt.encode(token_data,
                      AvishanConfig.JWT_KEY,
                      algorithm='HS256'
                      ).decode("utf8")


def decode_token():
    import jwt
    token = current_request['token']
    if not token:
        raise AuthException(AuthException.TOKEN_NOT_FOUND)
    try:
        from bpm_dev.avishan_config import AvishanConfig
        current_request['decoded_token'] = jwt.decode(token, AvishanConfig.JWT_KEY, algorithms=['HS256'])
    except jwt.exceptions.ExpiredSignatureError:
        AuthException(AuthException.TOKEN_EXPIRED)
    except:
        AuthException(AuthException.INVALID_TOKEN)


def find_and_check_user():
    """
    Populate current_request object with data from token. Then check for user "active" authorization
    :return:
    """
    from avishan.models import AvishanModel

    if not current_request['decoded_token']:
        AuthException(AuthException.INVALID_TOKEN)

    authentication_type_class = AvishanModel.find_model_with_class_name(
        current_request['decoded_token']['at_n']
    )
    try:
        authentication_type_object = authentication_type_class.objects.get(id=current_request['decoded_token']['at_id'])
        user_user_group = authentication_type_object.user_user_group
    except authentication_type_class.DoesNotExist:
        raise AuthException(AuthException.ACCOUNT_NOT_FOUND)

    if not user_user_group.is_active:
        raise AuthException(AuthException.GROUP_ACCOUNT_NOT_ACTIVE)
    if not user_user_group.base_user.is_active:
        raise AuthException(AuthException.ACCOUNT_NOT_ACTIVE)
    populate_current_request(authentication_type_object)


def populate_current_request(login_with: AuthenticationType):
    current_request['base_user'] = login_with.user_user_group.base_user
    current_request['user_group'] = login_with.user_user_group.user_group
    current_request['user_user_group'] = login_with.user_user_group
    current_request['authentication_object'] = login_with


def run_app_checks():
    # todo 0.2.0
    from core.avishan_config import check
    check()
