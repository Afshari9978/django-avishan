from typing import Union, Type

from django.http import JsonResponse

from avishan.exceptions import AvishanException


class AvishanView:
    def __init__(self, methods=None, authenticate: bool = None):
        if methods is None:
            methods = ['GET']
        self.methods = methods
        self.authenticate = authenticate
        self.is_api = None

    def __call__(self, view_function):

        def wrapper(*args, **kwargs):
            from .exceptions import AuthException
            from . import current_request

            try:
                if current_request['is_api'] is None:
                    current_request['is_api'] = self.is_api
                elif current_request['is_api'] is not self.is_api:
                    raise AuthException(AuthException.INAPPROPRIATE_PROTOCOL)
                """
                If user not provided, return with error. and also if api-type request but token in session instead of header
                """
                if self.authenticate and not self.is_authenticated():
                    raise AuthException(AuthException.ACCESS_DENIED)

                """http method check and raise 405"""
                if current_request['is_api'] and current_request['request'].method not in self.methods:
                    raise AuthException(AuthException.HTTP_METHOD_NOT_ALLOWED)
            except AuthException as e:
                return JsonResponse({})

            try:
                result = view_function(*args, **kwargs)
            except AvishanException as e:
                result = JsonResponse({})  # todo 0.2.4 capture all other exceptions too

            return result

        return wrapper

    @staticmethod
    def is_authenticated() -> bool:
        """
        Checks for user available in current_request storage
        :return: true if authenticated
        """
        from . import current_request
        if not current_request['authentication_object']:
            return False
        return True


class AvishanApiView(AvishanView):
    def __init__(self, methods=None, authenticate: bool = True):
        super().__init__(methods=methods, authenticate=authenticate)
        self.is_api = True


class AvishanTemplateView(AvishanView):
    def __init__(self, methods=None, authenticate: bool = True):
        super().__init__(methods=methods, authenticate=authenticate)
        self.is_api = False
