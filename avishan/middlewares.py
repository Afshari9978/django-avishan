import datetime
import json
import sys

from django.contrib import messages
from django.core.handlers.wsgi import WSGIRequest
from django.http import JsonResponse

from avishan.configure import get_avishan_config
from avishan.exceptions import AvishanException, save_traceback


class Wrapper:
    """this middleware creates "current_request" storage for each incoming request"""

    def __init__(self, get_response):
        self.get_response = get_response
        get_avishan_config().on_startup()

    def __call__(self, request: WSGIRequest):
        from avishan.utils import discard_monitor, find_token, decode_token, add_token_to_response, find_and_check_user
        from avishan import current_request

        start_time = datetime.datetime.now()

        self.initialize_request_storage(current_request)
        current_request['request'] = request
        current_request['language'] = request.GET.get('language', current_request['language'])

        """Checks for avoid-touch requests"""
        if discard_monitor(current_request['request'].get_full_path()):
            print(f"NOT_MONITORED: {current_request['request'].get_full_path()}")
            return self.get_response(current_request['request'])

        current_request['start_time'] = start_time

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
            save_traceback()
            AvishanException(e)

        if current_request['language'] is None:
            current_request['language'] = get_avishan_config().LANGUAGE

        get_avishan_config().on_request()

        # todo 0.2.2 check for 'avishan_' in request bodies
        """Send request object to the next layer and wait for response"""
        try:
            response = self.get_response(current_request['request'])
        except AvishanException:
            pass
        except Exception as e:
            save_traceback()
            AvishanException(e)

        """messages"""
        if current_request['messages']['debug'] or current_request['messages']['info'] or \
                current_request['messages']['success'] or current_request['messages']['warning'] or \
                current_request['messages']['error']:
            # todo 0.2.3: check for debug=True

            if current_request['is_api']:
                current_request['response']['messages'] = current_request['messages']
            else:
                self.fill_messages_framework(current_request)
                # todo fix problem on template: not showing thrown exception message

        add_token_to_response(response)
        status_code = current_request['status_code']
        is_api = current_request['is_api']
        json_safe = not current_request['json_unsafe']
        if current_request['is_api']:
            response = current_request['response'].copy()
        # else:
        #     messages.warning(current_request['request'], 'ای بابا')

        if current_request['is_tracked'] or current_request['exception'] is not None:
            self.save_request_track(current_request)

        self.initialize_request_storage(current_request)

        if is_api:
            return JsonResponse(response, status=status_code, safe=json_safe)
        elif response.status_code == 200 and status_code != 200:
            response.status_code = status_code

        return response

    @staticmethod
    def initialize_request_storage(current_request):
        from avishan.models import RequestTrack
        current_request.clear()
        current_request['request'] = None
        current_request['response'] = {}
        current_request['is_tracked'] = False

        """If not checked "None", then switches between api & template"""
        current_request['is_api'] = None

        current_request['add_token'] = False
        current_request['view_name'] = "NOT_AVAILABLE"
        current_request['start_time'] = None
        current_request['end_time'] = None
        current_request['view_start_time'] = None
        current_request['view_end_time'] = None
        current_request['json_unsafe'] = False
        current_request['base_user'] = None
        current_request['user_group'] = None
        current_request['user_user_group'] = None
        current_request['authentication_object'] = None
        current_request['exception_record'] = None
        current_request['token'] = None
        current_request['decoded_token'] = None
        current_request['status_code'] = 200
        current_request['exception'] = None
        current_request['traceback'] = None
        current_request['language'] = None
        current_request['request_track_object'] = RequestTrack()
        current_request['context'] = {}
        current_request['messages'] = {
            'debug': [], 'info': [], 'success': [], 'warning': [], 'error': []
        }

    @staticmethod
    def fill_messages_framework(current_request):
        for item in current_request['messages']['debug']:
            messages.debug(current_request['request'], item['body'])
        for item in current_request['messages']['info']:
            messages.info(current_request['request'], item['body'])
        for item in current_request['messages']['success']:
            messages.success(current_request['request'], item['body'])
        for item in current_request['messages']['warning']:
            messages.warning(current_request['request'], item['body'])
        for item in current_request['messages']['error']:
            messages.error(current_request['request'], item['body'])

    @staticmethod
    def save_request_track(current_request):
        from avishan.models import RequestTrackException
        for ignore in get_avishan_config().IGNORE_TRACKING_STARTS:
            if current_request['request'].get_full_path().startswith(ignore) and \
                    current_request['request_track_object']:
                current_request['request_track_object'].delete()
                return
        current_request['end_time'] = datetime.datetime.now()

        authentication_type_class_title = "NOT_AVAILABLE"
        authentication_type_object_id = 0
        if current_request['authentication_object']:
            authentication_type_class_title = current_request['authentication_object'].__class__.__name__
            authentication_type_object_id = current_request['authentication_object'].id

        try:
            request_data = json.dumps(current_request['request'].data, indent=2)
            request_data_size = sys.getsizeof(json.dumps(current_request['request'].data))
        except:
            request_data = "NOT_AVAILABLE"
            request_data_size = -1

        request_headers = ""
        for key, value in current_request['request'].META.items():
            if key.startswith('HTTP_'):
                request_headers += f'{key[5:]}={value}\n'
        for key in current_request['request'].FILES.keys():
            request_headers += f'FILE({key})\n'

        try:
            created = current_request['request_track_object'].update(
                view_name=current_request['view_name'],
                url=current_request['request'].get_full_path(),
                status_code=current_request['status_code'],
                method=current_request['request'].method,
                json_unsafe=current_request['json_unsafe'],
                is_api=current_request['is_api'],
                add_token=current_request['add_token'],
                user_user_group=current_request['user_user_group'],
                request_data=request_data,
                request_data_size=request_data_size,
                request_headers=request_headers,
                response_data=json.dumps(current_request['response'], indent=2),
                response_data_size=sys.getsizeof(json.dumps(current_request['response'])),
                start_time=current_request['start_time'],
                end_time=current_request['end_time'],
                total_execution_milliseconds=int((current_request['end_time'] - current_request[
                    'start_time']).total_seconds() * 1000),
                view_execution_milliseconds=int((current_request['view_end_time'] - current_request[
                    'view_start_time']).total_seconds() * 1000) if current_request['view_end_time'] else 0,
                authentication_type_class_title=authentication_type_class_title,
                authentication_type_object_id=authentication_type_object_id
            )

            if current_request['exception'] is not None:
                RequestTrackException.objects.create(
                    request_track=created,
                    class_title=current_request['exception'].__class__.__name__,
                    args=current_request['exception'].args,
                    traceback=current_request['traceback']
                )
        except Exception as e:
            print('save_request_track_error:'.upper(), e)
