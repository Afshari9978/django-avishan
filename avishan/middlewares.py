import json

from django.core.handlers.wsgi import WSGIRequest
from django.http import JsonResponse, QueryDict

# todo: try for import config
from .utils.data_functions import save_traceback
from avishan_config import USER_RESPONSE_DICT_FIELDS, MONITORED_URLS_START, NOT_MONITORED_URLS, \
    MONITORED_ANONYMOUS_URLS
from .exceptions import AuthException
from .models import UserUserGroup
from .utils.auth_functions import decode_token, verify_user, generate_token
from avishan_wrapper import current_request


# todo: disable unused middlewares and installed apps
# todo: bayad ye chizi dashte bashim k startup command bashe. role haro doros kone o yeseri kar bara re run
# todo readme ro doros konam
# todo: age ba ye esm, 2ta model dashtim che konim?
# todo: csrf chie? az middleware hazf she ya doros she?
# todo: 299 for message to user
# todo add username/password enter mode
# todo add email/otp enter mode
# todo have instant turn off exception record button

class AvishanMiddleware:
    def __init__(self, get_response):

        self.get_response = get_response
        from .utils.documentation_functions import create_raml_documentation
        # create_raml_documentation(PROJECT_NAME) todo: aya harbar bayad ejra she?

    def __call__(self, request: WSGIRequest):
        try:
            if must_have_token(request.path):
                try:
                    self.token = request.META['HTTP_TOKEN']
                except KeyError as e:
                    save_traceback()
                    raise AuthException(AuthException.TOKEN_ERROR)
                self.decoded_token = decode_token(self.token)
                try:
                    user_user_group = UserUserGroup.get(avishan_raise_exception=True,
                                                        id=self.decoded_token['user_user_group_id'])
                except UserUserGroup.DoesNotExist:
                    save_traceback()
                    raise AuthException(AuthException.ACCOUNT_NOT_FOUND)
                current_request['user'] = user_user_group.user

                # prints user data to log
                if user_user_group.user.have_profile:
                    print(
                        user_user_group.user.phone + " " + user_user_group.user.first_name + " " + user_user_group.user.last_name)
                else:
                    print(user_user_group.user.phone)

                current_request['user_group'] = user_user_group.user_group
                verify_user()

            self.data_fields_on_request(request)

            response = self.get_response(request)
            if response.status_code == 567:
                return JsonResponse({}, status=567)
            # todo inja k miad "status_code" 500 age bood male khodemoon nis dige
            # todo check response to to_dict models

            if isinstance(response, JsonResponse):
                # todo: merge response dict + current_request.response
                status_code = response.status_code
                if must_have_token(request.path):
                    current_request['response']['token'] = generate_token(self.decoded_token, self.token,
                                                                          current_request['user'],
                                                                          current_request['user_group'])
                    current_request['response']['user'] = current_request['user'].to_dict(
                        visible_list=USER_RESPONSE_DICT_FIELDS)
                    if current_request['execution_time'] > 0:
                        print("EXEC:", current_request['execution_time'])
                        current_request['response']['execution_time'] = current_request['execution_time']

                    return JsonResponse(current_request['response'], status=status_code)

                elif current_request['execution_time'] > 0:
                    print("EXEC:", current_request['execution_time'])
                    response = json.loads(response.content.decode('utf-8'))
                    response['execution_time'] = current_request['execution_time']
                    # clear_current_request(current_request)
                    return JsonResponse(response, status=status_code)
            # clear_current_request(current_request)
            return response
        except Exception as e:
            save_traceback()
            current_request['exception'] = e
            return JsonResponse({}, status=567)

    @staticmethod
    def data_fields_on_request(request: WSGIRequest):
        if request.method == 'GET':
            params = request.GET
        elif request.method == 'POST':
            params = request.POST
        elif request.method == 'PUT' or request.method == 'DELETE':
            params = QueryDict(request.body)

        request.search = params.get('search')
        request.page = params.get('page')
        request.page_size = params.get('page_size')
        request.filter = params.get('filter')
        request.sort = params.get('sort')

        if not request.search:
            request.search = ''
        if not request.page:
            request.page = 0
        if not request.page_size:
            request.page_size = 20
        if not request.filter:
            request.filter = []
        if not request.sort:
            request.sort = []


def must_monitor(url: str) -> bool:
    for start in MONITORED_URLS_START:
        if url.startswith(start):
            for not_monitored_start in NOT_MONITORED_URLS:
                if url.startswith(not_monitored_start):
                    return False
            return True
    return False


def must_have_token(url: str) -> bool:
    if must_monitor(url):
        for start in MONITORED_ANONYMOUS_URLS:
            if url.startswith(start):
                return False
    else:
        return False
    return True
