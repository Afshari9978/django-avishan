from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect

from avishan.exceptions import AvishanException, save_traceback, AuthException
from avishan_admin_config import AvishanAdminConfig

try:
    from avishan_admin.avishan_config import AvishanConfig as PanelAvishanConfig
except ImportError:
    pass


class Wrapper:
    """this middleware creates "current_request" storage for each incoming request"""

    def __init__(self, get_response):
        self.get_response = get_response

        """
        Run avishan_config files, 'check' method. And also creates config file if not found
        """
        from avishan.models import AvishanModel
        AvishanModel.run_apps_check()

    def __call__(self, request):
        from avishan.utils import discard_monitor, find_token, decode_token, add_token_to_response, find_and_check_user
        from avishan import current_request

        self.initialize_request_storage(current_request)
        current_request['request'] = request

        """Checks for avoid-touch requests"""
        if discard_monitor(current_request['request'].path):
            return self.get_response(current_request['request'])

        """Find token and parse it"""
        """
        Bara inke yadam nare. tooye sathe middleware vaghti error midim, chon nemidoonim api e ya template, error ro 
        zakhire mikonim mirim decorator, baad oonja k set shod in meghdar, check mikonim chon error hast, barmigarde 
        inja 
        """
        try:
            if find_token():
                decode_token()
                find_and_check_user()
        except AvishanException:
            pass
        except Exception as e:
            # import traceback
            # summary = traceback.StackSummary.extract(
            #     traceback.walk_stack(None)
            # )
            save_traceback()
            AvishanException(e)

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
        except AvishanException:
            pass
        except Exception as e:
            # import traceback
            # summary = traceback.StackSummary.extract(
            #     traceback.walk_stack(None)
            # )
            save_traceback()
            AvishanException(e)
        delete_token = False
        if current_request['exception'] is not None:
            if isinstance(current_request['exception'], AuthException):
                delete_token = True
                """
                According to messages framework doc, iterating over messages, will clear them.
                """
                for item in messages.get_messages(request):
                    pass
                response = redirect(
                    '/' + AvishanAdminConfig.ADMIN_PANEL_ROOT_ADDRESS + '/' +
                    AvishanAdminConfig.ADMIN_PANEL_LOGIN_ADDRESS
                )
            else:
                if not current_request['discard_json_object_check']:
                    current_request['response']['error'] = current_request['errors']
                    response = JsonResponse(current_request['response'], status=current_request['status_code'],
                                            safe=not current_request['discard_json_object_check'])

        add_token_to_response(response, delete_token)
        status_code = current_request['status_code']
        is_api = current_request['is_api']
        json_safe = not current_request['discard_json_object_check']
        if current_request['is_api']:
            response = current_request['response'].copy()

        self.initialize_request_storage(current_request)

        if is_api:
            return JsonResponse(response, status=status_code, safe=json_safe)
        elif response.status_code == 200 and status_code != 200:
            response.status_code = status_code

        return response

    @staticmethod
    def initialize_request_storage(current_request):
        current_request.clear()
        current_request['request'] = None
        current_request['response'] = {}

        """If not checked "None", then switches between api & template"""
        current_request['is_api'] = None

        current_request['add_token'] = False
        current_request['discard_json_object_check'] = False
        current_request['base_user'] = None
        current_request['user_group'] = None
        current_request['authentication_object'] = None
        current_request['exception_record'] = None
        current_request['user_user_group'] = None
        current_request['token'] = None
        current_request['decoded_token'] = None
        current_request['status_code'] = 200
        current_request['exception'] = None
        current_request['traceback'] = None
        current_request['context'] = {}
        current_request['errors'] = []
        current_request['warnings'] = []
        current_request['alerts'] = []
