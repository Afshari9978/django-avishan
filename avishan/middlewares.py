from avishan import current_request, thread_storage


class Wrapper:
    """this middleware creates "current_request" storage for each incoming request"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        current_request['request'] = request
        current_request['response'] = {}
        current_request['discard_wsgi_response'] = True
        current_request['base_user'] = None
        current_request['user_group'] = None
        current_request['user_user_group'] = None
        current_request['status_code'] = 200

        # todo: create request.data from request body

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
        from avishan.utils import must_have_token, is_token_in_header, is_token_in_session, add_token_to_response, \
            must_monitor

        """Checks for avoid-touch requests"""
        if not must_monitor(request.path):
            return self.get_response(request)

        """Check if this request must contain token with it"""
        if must_have_token(request.path):
            if is_token_in_header():
                pass  # todo

            elif is_token_in_session():
                pass  # todo

            else:
                pass  # todo Token not found; raise exception

            # todo Find user and manipulate current_request object
            # todo Check if user can use system. (is_active)

        """Send request object to the next layer and wait for response"""
        response = self.get_response(request)

        if current_request['discard_wsgi_response']:
            # todo: Return current_request response as response. Should decode response and encoded it again
            pass

        add_token_to_response()

        return response
