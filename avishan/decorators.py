import datetime
import json

from django.http import JsonResponse

from avishan.exceptions import AvishanException, AuthException
from . import current_request
from .models import RequestTrack


class AvishanViewDecorator:
    def __init__(self, is_api: bool, methods=('GET',), authenticate: bool = None, track_it: bool = False):
        self.methods = methods
        self.authenticate = authenticate
        self.is_api = is_api
        self.track_it = track_it

    def __call__(self, view_function):

        def wrapper(*args, **kwargs):
            current_request['view_name'] = view_function.__name__
            current_request['request_track_exec'] = [
                {'title': 'begin', 'now': datetime.datetime.now()}
            ]
            current_request['is_api'] = self.is_api
            if self.track_it and not current_request['is_tracked']:
                current_request['is_tracked'] = True
                current_request['request_track_object'] = RequestTrack.objects.create()
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

                current_request['view_start_time'] = datetime.datetime.now()
                result = view_function(*args, **kwargs)
                current_request['view_end_time'] = datetime.datetime.now()

                if self.track_it:
                    current_request['request_track_object'].create_exec_infos(current_request['request_track_exec'])

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


class AvishanApiViewDecorator(AvishanViewDecorator):

    def __init__(self, methods=('GET',), authenticate: bool = True, track_it: bool = False):
        super().__init__(is_api=True, methods=methods, authenticate=authenticate, track_it=track_it)

    def before_request(self):
        if current_request['request'].method not in ['GET', 'DELETE']:
            try:
                if len(current_request['request'].body) > 0:
                    current_request['request'].data = json.loads(current_request['request'].body.decode('utf-8'))
                else:
                    current_request['request'].data = {}
            except:
                current_request['request'].data = {}

    def after_request(self):
        pass

    def before_response(self):
        pass

    def after_response(self):
        pass


class AvishanTemplateViewDecorator(AvishanViewDecorator):
    def __init__(self, methods=('GET',), authenticate: bool = True, track_it: bool = False):
        super().__init__(is_api=False, methods=methods, authenticate=authenticate, track_it=track_it)

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
            except:
                current_request['request'].data = {}

    def after_request(self):
        pass

    def before_response(self):
        pass

    def after_response(self):
        pass
