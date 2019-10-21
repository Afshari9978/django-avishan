from typing import Type

from avishan.exceptions import AvishanException
from . import current_request


def must_monitor(url: str) -> bool:
    """
    checks if request is in check-blacklist
    :param url: request url
    :return:
    """


def must_have_token(url: str) -> bool:
    """
    checks if request with this url must have token included.
    :param url: request url
    :return:
    """
    pass  # todo


def find_token_in_header() -> bool:
    """
    find token and put it in current_request
    :return: false if token not found
    """
    try:
        current_request['token'] = current_request['request'].META['HTTP_TOKEN']
        return True
    except KeyError as e:
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
    except KeyError as e:
        pass

    return False


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
