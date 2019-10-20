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


def is_token_in_header() -> bool:
    """
    find token and put it in current_request
    :return: false if token not found
    """
    pass  # todo


def is_token_in_session() -> bool:
    """
    find token and put it in current_request
    :return: false if token not found
    """
    pass  # todo


def add_token_to_response():
    """
    create new token if needed, else reuse previous
    add token to session if session-based auth, else to response header
    """
    pass  # todo
