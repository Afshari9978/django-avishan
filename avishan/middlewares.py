import datetime
import json
import sys
from typing import Optional, Union

from crum import get_current_request, set_current_request
from django.contrib import messages
from django.core.handlers.wsgi import WSGIRequest
from django.http import JsonResponse
from django.utils import timezone


class Wrapper:
    """this middleware creates "current_request" storage for each incoming request"""

    def __init__(self, get_response):
        from avishan.configure import get_avishan_config

        self.get_response = get_response
        get_avishan_config().on_startup()

        """Run Descriptor to find any error in startup and store project"""
        from avishan.descriptor import Project
        self.project = Project(name=get_avishan_config().PROJECT_NAME)
        get_avishan_config().PROJECT = self.project

    def __call__(self, request: WSGIRequest):
        from avishan.utils import discard_monitor, find_token, decode_token, add_token_to_response, find_and_check_user
        from avishan.exceptions import AvishanException
        from avishan.exceptions import save_traceback
        from avishan.configure import get_avishan_config

        request.avishan = AvishanRequestStorage(request)
        request.avishan.project = self.project

        """Checks for avoid-touch requests"""
        if discard_monitor(request.get_full_path()):
            print(f"NOT_MONITORED: {request.get_full_path()}")
            response = self.get_response(request)
            if 'token' in request.COOKIES.keys():
                response.set_cookie('token', request.COOKIES['token'])
            del request.avishan
            return response

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

        get_avishan_config().on_request(request)

        # todo 0.2.2 check for 'avishan_' in request bodies
        """Send request object to the next layer and wait for response"""
        try:
            response = self.get_response(request)
            if not request.avishan.can_touch_response:
                del request.avishan
                return response
        except AvishanException:
            pass
        except Exception as e:
            save_traceback()
            AvishanException(e)

        remove_from_crum = False
        if get_current_request() is None:
            remove_from_crum = True
            set_current_request(request)

        """messages"""
        if request.avishan.have_message():
            # todo 0.2.3: check for debug=True

            if request.avishan.is_api:
                request.avishan.response['messages'] = request.avishan.messages
            else:
                # noinspection PyTypeChecker
                self.fill_messages_framework(request)
                if request.avishan.on_error_view_class and response.status_code == 500:
                    response = request.avishan.on_error_view_class.render()
                # todo fix problem on template: not showing thrown exception message

        add_token_to_response(response)
        status_code = request.avishan.status_code
        is_api = request.avishan.is_api
        json_safe = not request.avishan.json_unsafe
        if is_api:
            response = request.avishan.response.copy()

        if request.avishan.is_tracked or request.avishan.exception is not None:
            self.save_request_track(request)

        del request.avishan
        if remove_from_crum:
            set_current_request(None)

        if is_api:
            return JsonResponse(response, status=status_code, safe=json_safe)

        """Do not change redirection status codes"""
        if response.status_code // 100 != 3:
            response.status_code = status_code
        return response

    @staticmethod
    def fill_messages_framework(request):
        for item in request.avishan.messages['debug']:
            messages.debug(request, item['body'])
        for item in request.avishan.messages['info']:
            messages.info(request, item['body'])
        for item in request.avishan.messages['success']:
            messages.success(request, item['body'])
        for item in request.avishan.messages['warning']:
            messages.warning(request, item['body'])
        for item in request.avishan.messages['error']:
            messages.error(request, item['body'])

    @staticmethod
    def save_request_track(request: WSGIRequest):
        from avishan.configure import get_avishan_config
        # noinspection PyTypeHints
        request.avishan: AvishanRequestStorage
        from avishan.models import RequestTrackException
        for ignore in get_avishan_config().IGNORE_TRACKING_STARTS:
            if request.get_full_path().startswith(ignore) and \
                    request.avishan.request_track_object:
                request.avishan.request_track_object.delete()
                return
        request.avishan.end_time = timezone.now()

        authentication_type_class_title = "NOT_AVAILABLE"
        authentication_type_object_id = 0
        if request.avishan.authentication_object:
            authentication_type_class_title = request.avishan.authentication_object.__class__.__name__
            authentication_type_object_id = request.avishan.authentication_object.id

        request_data = "NOT_AVAILABLE"
        request_data_size = -1
        if request.method in ['POST', 'PUT']:
            try:
                request_data = json.dumps(request.data, indent=2)
                request_data_size = sys.getsizeof(json.dumps(request.data))
            except:
                print("*DEBUG* request parse error")

        request_headers = ""
        for key, value in request.META.items():
            if key.startswith('HTTP_'):
                request_headers += f'{key[5:]}={value}\n'
        for key in request.FILES.keys():
            request_headers += f'FILE({key})\n'

        from avishan.views.class_based import AvishanView
        if request.avishan.view_class:
            view_name = request.avishan.view_class.__class__.__name__ \
                if isinstance(request.avishan.view_class, AvishanView) \
                else request.avishan.view_class.__name__
        else:
            view_name = None

        try:
            response_data = json.dumps(request.avishan.response, indent=2)
        except:
            print("*DEBUG* response parse error:", request.avishan.response)
            response_data = 'NOT_AVAILABLE'

        try:
            created = request.avishan.request_track_object.update(
                view_name=view_name,
                url=request.get_full_path(),
                status_code=request.avishan.status_code,
                method=request.method,
                json_unsafe=request.avishan.json_unsafe,
                is_api=request.avishan.is_api,
                add_token=request.avishan.add_token,
                user_user_group=request.avishan.user_user_group,
                request_data=request_data,
                request_data_size=request_data_size,
                request_headers=request_headers,
                response_data=response_data,
                response_data_size=sys.getsizeof(response_data),
                start_time=request.avishan.start_time,
                end_time=request.avishan.end_time,
                total_execution_milliseconds=int(
                    (request.avishan.end_time - request.avishan.start_time).total_seconds() * 1000),
                view_execution_milliseconds=int(
                    (request.avishan.view_end_time - request.avishan.view_start_time).total_seconds() * 1000)
                if request.avishan.view_end_time else 0,
                authentication_type_class_title=authentication_type_class_title,
                authentication_type_object_id=authentication_type_object_id
            )

            if request.avishan.exception is not None:
                RequestTrackException.objects.create(
                    request_track=created,
                    class_title=request.avishan.exception.__class__.__name__,
                    args=request.avishan.exception.args,
                    traceback=request.avishan.traceback
                )
        except Exception as e:
            print('save_request_track_error:'.upper(), e)


class AvishanRequestStorage:
    def __init__(self, request: WSGIRequest):
        from avishan.views.class_based import AvishanView, AvishanTemplateView
        from avishan.models import BaseUser, UserGroup, UserUserGroup, EmailKeyValueAuthentication, \
            PhoneKeyValueAuthentication, EmailOtpAuthentication, PhoneOtpAuthentication, VisitorKeyAuthentication, \
            RequestTrack
        from avishan.descriptor import Project
        from avishan.configure import get_avishan_config
        from avishan.exceptions import AvishanException

        self.project: Optional[Project] = None
        self.request: WSGIRequest = request
        self.response: dict = {}
        self.parsed_data: Optional[dict] = None
        self.language: str = request.GET.get('language') or request.GET.get('lng') or get_avishan_config().LANGUAGE
        self.can_touch_response: bool = True
        self.is_tracked: bool = True
        self.add_token: bool = False

        self.is_api: Optional[bool] = None
        self.view_class: Optional[AvishanView] = None
        self.on_error_view_class: Optional[AvishanTemplateView] = None
        self.json_unsafe: bool = False
        self.token: Optional[str] = None
        self.decoded_token: Optional[dict] = None
        self.status_code: int = 200
        self.context: dict = {}
        self.messages: dict = {
            'debug': [], 'info': [], 'success': [], 'warning': [], 'error': []
        }

        self.start_time: datetime.datetime = timezone.now()
        self.end_time: Optional[datetime.datetime] = None
        self.view_start_time: Optional[datetime.datetime] = None
        self.view_end_time: Optional[datetime.datetime] = None

        self.base_user: Optional[BaseUser] = None
        self.user_group: Optional[UserGroup] = None
        self.user_user_group: Optional[UserUserGroup] = None
        self.authentication_object: Optional[Union[
            EmailKeyValueAuthentication,
            PhoneKeyValueAuthentication,
            EmailOtpAuthentication,
            PhoneOtpAuthentication,
            VisitorKeyAuthentication
        ]] = None

        self.request_track_object: RequestTrack = RequestTrack()
        self.exception: Optional[AvishanException] = None
        self.traceback: Optional[str] = None
        self.debug: bool = False

    def have_message(self) -> bool:
        return self.messages['debug'] or self.messages['info'] or self.messages['success'] or \
               self.messages['warning'] or self.messages['error']
