from avishan import current_request, thread_storage


class Wrapper:
    """this middleware creates "current_request" storage for each incoming request"""

    def __init__(self, get_response):
        self.get_response = get_response

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
        current_request['status_code'] = 200

        """
        Parse request data
        """
        if request.method != 'GET':
            try:
                if len(request.body) > 0:
                    request.data = json.loads(request.body.decode('utf-8'))
                else:
                    request.data = {}
            except RawPostDataException:
                request.data = {}

        """Send request object to the next layer and wait for response"""
        response = self.get_response(request)

        """Delete current_request from it's thread"""
        if hasattr(thread_storage, 'current_request'):
            del thread_storage.current_request

        return response


class Authentication:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from avishan.utils import must_have_token, find_token_in_header, find_token_in_session, add_token_to_response, \
            must_monitor

        """Checks for avoid-touch requests"""
        if not must_monitor(request.path):
            return self.get_response(request)

        """Check if this request must contain token with it"""
        if must_have_token(request.path):
            if not find_token_in_header() and not find_token_in_session():
                pass  # todo Token not found; raise exception

            # todo: decode token and check it
            # todo Find user and manipulate current_request object

        """Send request object to the next layer and wait for response"""
        response = self.get_response(request)

        add_token_to_response()

        return response
