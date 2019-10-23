from avishan.utils import save_traceback_and_raise_exception


class AvishanView:
    def __init__(self, methods=None, authenticate: bool = None):
        if methods is None:
            methods = ['GET']
        self.methods = methods
        self.authenticate = authenticate

    def __call__(self, view_function):

        def wrapper(*args, **kwargs):
            from .exceptions import AvishanException, AuthException
            from . import current_request

            """If user not provided, return with error. and also if api-type but token in session"""
            if self.authenticate and not self.is_authenticated():
                raise AuthException(AuthException.ACCESS_DENIED)

            """http method check and raise 405"""
            if current_request['request'].method not in self.methods:
                raise AuthException(AuthException.HTTP_METHOD_NOT_ALLOWED)

            try:
                result = view_function(*args, **kwargs)
            except AvishanException as e:
                save_traceback_and_raise_exception(e)  # todo: should return to next level middleware
            except Exception as e:
                save_traceback_and_raise_exception(AvishanException(wrap_exception=e))

            return result

        return wrapper

    @staticmethod
    def is_authenticated() -> bool:
        """
        Checks for user available in current_request storage
        :return: true if authenticated
        """
        from . import current_request
        if not current_request['base_user']:
            return False
        return True


class AvishanApiView(AvishanView):
    def __init__(self, methods=None, authenticate: bool = True):
        self.type = 'api'
        super().__init__(methods=methods, authenticate=authenticate)


class AvishanTemplateView(AvishanView):
    def __init__(self, methods=None, authenticate: bool = True):
        self.type = 'template'
        super().__init__(methods=methods, authenticate=authenticate)


class AvishanCalculate:
    # todo: execution time
    pass
