import json

from django.http import JsonResponse, RawPostDataException

from avishan.exceptions import AvishanException, AuthException, save_traceback
from . import current_request


class AvishanView:
    def __init__(self, is_api: bool, methods=None, authenticate: bool = None):
        if methods is None:
            methods = ['GET']
        self.methods = methods
        self.authenticate = authenticate
        self.is_api = is_api

    def __call__(self, view_function):

        def wrapper(*args, **kwargs):
            current_request['is_api'] = self.is_api
            if current_request['exception']:
                """If we have exception here, should return after "is_api" assignment to middleware"""
                return JsonResponse({})

            try:
                """
                If user not provided, return with error.
                """
                # todo 0.2.4: if api-type request but token in session instead of header
                self.before_request()

                if self.authenticate and not self.is_authenticated():
                    raise AuthException(AuthException.ACCESS_DENIED)

                """http method check and raise 405"""
                if current_request['is_api'] and current_request['request'].method not in self.methods:
                    raise AuthException(AuthException.HTTP_METHOD_NOT_ALLOWED)

                self.after_request()

                result = view_function(*args, **kwargs)

                self.before_response()

                self.after_response()

            except AvishanException:
                return JsonResponse({})
            except Exception as e:
                AvishanException(wrap_exception=e)
                return JsonResponse({})
            if current_request['exception']:
                return JsonResponse({})

            return result

        return wrapper

    def before_request(self):
        raise NotImplementedError()

    def after_request(self):
        raise NotImplementedError()

    def before_response(self):
        raise NotImplementedError()

    def after_response(self):
        raise NotImplementedError()

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
        super().__init__(is_api=True, methods=methods, authenticate=authenticate)

    def before_request(self):
        if current_request['request'].method not in ['GET', 'DELETE']:
            try:
                if len(current_request['request'].body) > 0:
                    current_request['request'].data = json.loads(current_request['request'].body.decode('utf-8'))
                else:
                    current_request['request'].data = {}
            except RawPostDataException:
                current_request['request'].data = {}
            except:
                pass

    def after_request(self):
        pass

    def before_response(self):
        pass

    def after_response(self):
        pass


class AvishanTemplateView(AvishanView):
    def __init__(self, methods=None, authenticate: bool = True):
        super().__init__(is_api=False, methods=methods, authenticate=authenticate)

    def before_request(self):
        if current_request['request'].method in ['POST', 'PUT']:
            try:
                if len(current_request['request'].body) > 0:
                    current_request['request'].data = dict(current_request['request'].POST)
                    for key, value in current_request['request'].data.items():
                        if len(value) == 1:
                            current_request['request'].data[key] = value[0]
                else:
                    current_request['request'].data = {}
            except RawPostDataException:
                current_request['request'].data = {}
            except:
                pass

    def after_request(self):
        pass

    def before_response(self):
        pass

    def after_response(self):
        pass
