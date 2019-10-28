from django.http import JsonResponse


class AvishanView:
    def __init__(self, methods=None, authenticate: bool = None):
        if methods is None:
            methods = ['GET']
        self.methods = methods
        self.authenticate = authenticate
        self.is_api = None

    def __call__(self, view_function):

        def wrapper(*args, **kwargs):
            from .exceptions import AuthException, AvishanException
            from . import current_request
            from bpm_dev.avishan_config import AvishanConfig
            from django.shortcuts import redirect

            current_request['is_api'] = self.is_api if current_request['is_api'] is None else current_request['is_api']

            """
            If user not provided, return with error. and also if api-type request but token in session instead of header
            """
            if self.authenticate and not self.is_authenticated():
                if current_request['is_api']:
                    raise AuthException(AuthException.ACCESS_DENIED)
                return redirect(AvishanConfig.TEMPLATE_LOGIN_PAGE)

            """http method check and raise 405"""
            if current_request['is_api'] and current_request['request'].method not in self.methods:
                raise AuthException(AuthException.HTTP_METHOD_NOT_ALLOWED)

            try:
                result = view_function(*args, **kwargs)
            except AvishanException as e:
                current_request['exception'] = e
                result = JsonResponse({})
                # todo: should return to next level middleware 0.2.0
            except Exception as e:
                current_request['exception'] = e
                result = JsonResponse({})

            return result

        return wrapper

    @staticmethod
    def is_authenticated() -> bool:
        """
        Checks for user available in current_request storage
        :return: true if authenticated
        """
        from . import current_request
        if not current_request['user_user_group']:
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


class AvishanCalculate:
    # todo: execution time 0.2.3
    pass
