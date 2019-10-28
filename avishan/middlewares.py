from django.http import JsonResponse

from avishan import current_request, thread_storage


class Wrapper:
    """this middleware creates "current_request" storage for each incoming request"""

    def __init__(self, get_response):
        from avishan.utils import run_app_checks
        self.get_response = get_response

        """
        Run avishan_config files, 'check' method
        """
        run_app_checks()

    def __call__(self, request):
        from django.http.request import RawPostDataException
        import json

        current_request['request'] = request
        current_request['response'] = {}

        """If not checked "None", then switches between api & template"""
        current_request['is_api'] = None

        current_request['discard_wsgi_response'] = True
        current_request['base_user'] = None
        current_request['user_group'] = None
        current_request['user_user_group'] = None
        current_request['token'] = None
        current_request['decoded_token'] = None
        current_request['status_code'] = 200
        current_request['exception'] = None
        current_request['authentication_object'] = None

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

        """Send request object to the next layer and wait for response"""
        response = self.get_response(request)

        if current_request['exception']:
            temp = {
                'exception': current_request['exception'].args
            }
            if hasattr(thread_storage, 'current_request'):
                del thread_storage.current_request
            return JsonResponse(temp)

        """Delete current_request from it's thread"""
        if hasattr(thread_storage, 'current_request'):
            del thread_storage.current_request

        return response


class Authentication:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from avishan.utils import find_token, add_token_to_response, must_monitor, find_and_check_user, decode_token

        """Checks for avoid-touch requests"""
        if not must_monitor(request.path):
            return self.get_response(request)

        """Find token and parse it"""
        if find_token():
            decode_token()
            find_and_check_user()

        """Send request object to the next layer and wait for response"""
        response = self.get_response(request)

        if current_request['user_user_group']:
            add_token_to_response(response)

        return response
