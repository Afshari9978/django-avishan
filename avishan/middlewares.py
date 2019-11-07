from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import redirect

from avishan import thread_storage
from avishan_config import AvishanConfig


class Wrapper:
    """this middleware creates "current_request" storage for each incoming request"""

    def __init__(self, get_response):
        self.get_response = get_response

        """
        Run avishan_config files, 'check' method
        """
        from avishan.models import AvishanModel
        AvishanModel.run_apps_check()

    def __call__(self, request):
        from django.http.request import RawPostDataException
        from . import current_request
        import json

        self.clear_current_request(current_request)
        current_request['request'] = request

        """
        Parse request data
        """
        if request.method != 'GET':
            try:
                if len(request.body) > 0 and not request.body.decode('utf-8').startswith('csrfmiddlewaretoken'):
                    request.data = json.loads(request.body.decode('utf-8'))
                else:
                    request.data = {}
            except RawPostDataException:
                request.data = {}
            except:  # todo 0.2.3 in html forms, it raises errors
                pass

        # todo 0.2.2 check for 'avishan_' in request bodies
        """Send request object to the next layer and wait for response"""
        response = self.get_response(request)

        if current_request['discard_wsgi_response'] and not (
                isinstance(response, HttpResponseRedirect) and current_request['is_api'] is False):
            response = current_request['response']
            self.clear_current_request(current_request)
            return JsonResponse(response)

        self.clear_current_request(current_request)

        return response

    @staticmethod
    def clear_current_request(current_request):
        current_request['request'] = None
        current_request['response'] = {}

        """If not checked "None", then switches between api & template"""
        current_request['is_api'] = None

        current_request['discard_wsgi_response'] = False
        current_request['base_user'] = None
        current_request['user_group'] = None
        current_request['user_user_group'] = None
        current_request['token'] = None
        current_request['decoded_token'] = None
        current_request['status_code'] = 200
        current_request['exception'] = None
        current_request['authentication_object'] = None


class Authentication:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from avishan.utils import find_token, add_token_to_response, must_monitor, find_and_check_user, decode_token
        from . import current_request
        from avishan.exceptions import AvishanException
        from avishan.utils import delete_token_from_request

        """Checks for avoid-touch requests"""
        if not must_monitor(request.path):
            return self.get_response(request)

        """Find token and parse it"""
        delete_cookie = False
        try:
            if find_token():
                decode_token()
                find_and_check_user()
        except AvishanException as e:
            current_request['exception'] = e
            if current_request['is_api'] is False:
                current_request['discard_wsgi_response'] = False
                response = redirect(AvishanConfig.TEMPLATE_LOGIN_URL, permanent=True)
                delete_token_from_request(response)
                return response
            return JsonResponse({})  # todo 0.2.4 other exceptions too

        """Send request object to the next layer and wait for response"""
        response = self.get_response(request)

        if current_request['user_user_group']:
            add_token_to_response(response, delete_cookie)

        return response
