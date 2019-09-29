import jwt

from avishan.models.users import User, UserGroup, UserUserGroup
from .data_functions import save_traceback
from avishan_config import JWT_KEY
from ..exceptions import AuthException
from .bch_datetime import BchDatetime


def verify_user(user_object: User = None, try_on_group: UserGroup = None) -> UserUserGroup:
    if not user_object and not try_on_group:
        from avishan_wrapper import current_request
        user_object = current_request['user']
        try_on_group = current_request['user_group']

    if not user_object.is_active:
        raise AuthException(AuthException.ACCOUNT_NOT_ACTIVE)
    try:
        return UserUserGroup.get(
            avishan_raise_exception=True, user=user_object, user_group=try_on_group
        )
    except UserUserGroup.DoesNotExist:
        save_traceback()
        raise AuthException(AuthException.UNAUTHORIZED_ROLE)


def encode_token(user_user_group: UserUserGroup) -> str:
    now = BchDatetime()
    user_user_group.date_last_used = now.to_datetime()
    user_user_group.save()
    token_data = {
        'created_at': now.to_unix_timestamp(),
        'exp': '', # todo
        'id': user_user_group.id
    }
    return jwt.encode(token_data,
                      JWT_KEY,
                      algorithm='HS256'
                      ).decode("utf-8")


def decode_token(token: str) -> dict:
    if not token:
        print("token: " + token)
        raise AuthException(AuthException.INCORRECT_TOKEN)
    try:
        return jwt.decode(token, JWT_KEY, algorithms=['HS256'])
    except jwt.exceptions.ExpiredSignatureError:
        save_traceback()
        raise AuthException(AuthException.TOKEN_EXPIRED)
    except:
        print("token: " + token)
        save_traceback()
        raise AuthException(AuthException.TOKEN_ERROR)


def generate_token(decoded_token, token, user: User, user_group: UserGroup) -> str:
    # todo is it efficient to create a new token
    return encode_token(UserUserGroup.objects.get(user=user, user_group=user_group))
