from . import current_request, thread_storage


class AvishanWrapper:
    """
    this middleware creates "current_request" storage for each incoming request
    """

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

        response = self.get_response(request)

        if hasattr(thread_storage, 'current_request'):
            del thread_storage.current_request

        return response
