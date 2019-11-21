from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import redirect

from avishan.exceptions import AvishanException

try:
    from avishan_admin.avishan_config import AvishanConfig as PanelAvishanConfig
except ImportError:
    pass


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
        from avishan.utils import must_monitor, find_token, decode_token, add_token_to_response, find_and_check_user
        from avishan import current_request
        from avishan.exceptions import AuthException
        import json

        self.initialize_request_storage(current_request)
        current_request['request'] = request

        """Checks for avoid-touch requests"""
        if not must_monitor(current_request['request'].path):
            return self.get_response(current_request['request'])

        """Find token and parse it"""
        try:
            if find_token():
                decode_token()
                find_and_check_user()
        except AuthException as e:
            pass  # todo 0.2.0: ey khoda

        """
        Parse request data
        """
        if current_request['request'].method not in ['GET', 'DELETE'] and current_request['is_api']:
            try:
                if len(current_request['request'].body) > 0:
                    current_request['request'].data = json.loads(current_request['request'].body.decode('utf-8'))
                else:
                    current_request['request'].data = {}
            except RawPostDataException:
                current_request['request'].data = {}
            except:
                pass
        try:
            """
            If avishan_admin installed and check method found, run it.
            """
            from avishan_admin.avishan_config import check_request
            check_request()
        except ImportError:
            pass

        # todo 0.2.2 check for 'avishan_' in request bodies
        """Send request object to the next layer and wait for response"""
        try:
            response = self.get_response(current_request['request'])
        except AvishanException as e:
            # todo 0.2.0: what to do
            pass
        except Exception as e:
            e = AvishanException(e)
            pass

        if current_request['exception'] is not None:
            if isinstance(current_request['exception'], AuthException):
                if current_request['is_api'] is False:
                    try:
                        return redirect('/' + PanelAvishanConfig.PANEL_ROOT + "/" + PanelAvishanConfig.LOGIN_URL)
                    except:
                        raise current_request['exception']

        add_token_to_response(response)
        if current_request['is_api']:
            response = current_request['response'].copy()

        self.initialize_request_storage(current_request)

        if current_request['is_api']:
            return JsonResponse(current_request['response'])

        return response

    @staticmethod
    def initialize_request_storage(current_request):
        current_request.clear()
        current_request['request'] = None
        current_request['response'] = {}

        """If not checked "None", then switches between api & template"""
        current_request['is_api'] = None

        current_request['add_token'] = False
        current_request['base_user'] = None
        current_request['user_group'] = None
        current_request['user_user_group'] = None
        current_request['token'] = None
        current_request['decoded_token'] = None
        current_request['status_code'] = 200
        current_request['exception'] = None
        current_request['authentication_object'] = None
        current_request['context'] = {}
        current_request['error'] = None
        current_request['warning'] = None
