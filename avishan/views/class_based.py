import datetime
import inspect
import json
from typing import List, get_type_hints, Type, Callable, Optional

from django.core.handlers.wsgi import WSGIRequest
from django.db import models
from django.db.models import QuerySet
from django.http import JsonResponse
from django.views import View

from avishan import current_request
from avishan.configure import get_avishan_config
from avishan.descriptor import DirectCallable
from avishan.exceptions import ErrorMessageException, AvishanException, AuthException
from avishan.libraries.openapi3.classes import ApiDocumentation, Path, PathGetMethod, PathResponseGroup, \
    PathResponse, Content, Schema, PathPostMethod, PathRequest, PathPutMethod, PathDeleteMethod
from avishan.misc import status
from avishan.misc.translation import AvishanTranslatable
from avishan.models import AvishanModel, RequestTrack


# todo fix cors motherfucker
# todo doc
class AvishanView(View):
    authenticate: bool = True
    track_it: bool = False
    is_api: bool = None

    # todo can override http_method_not_allowed method
    # todo implement time logs here
    search: List[str] = None
    filter: List[dict] = []
    # todo add gte lte ... to filter
    sort: List[str] = []
    page: int = 0
    page_size: int = 20
    page_offset: int = 0

    # todo if page is not 0, send page, page size, items count, next, prev

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.response: dict = current_request['response']
        self.request: WSGIRequest
        self.class_attributes_type = get_type_hints(self.__class__)

        for kwarg_key, kwarg_value in kwargs.items():
            if hasattr(self, kwarg_key):
                self.__setattr__(kwarg_key, kwarg_value)

        for kwarg_key in request.GET.keys():
            kwarg_key: str
            if hasattr(self, kwarg_key):
                data = request.GET.getlist(kwarg_key)
                if len(data) > 1:
                    parsed = []
                    for item in data:
                        parsed.append(self.cast_data(kwarg_key, item))
                    self.__setattr__(kwarg_key, parsed)
                else:
                    self.__setattr__(kwarg_key, self.cast_data(kwarg_key, data[0]))

            if kwarg_key.startswith('filter_'):
                data = request.GET.getlist(kwarg_key)
                if len(data) == 1:
                    data = data[0]
                self.filter.append({kwarg_key[7:]: data})

            if kwarg_key.startswith('sort_'):
                data = request.GET.getlist(kwarg_key)
                if len(data) == 1:
                    data = data[0]
                self.filter.append({kwarg_key[5:]: data})

        self.current_request = current_request
        self.current_request['view_name'] = self.__class__.__name__
        self.current_request['request_track_exec'] = [
            {'title': 'begin', 'now': datetime.datetime.now()}
        ]
        self.current_request['is_api'] = self.is_api
        if self.track_it and not self.current_request['is_tracked']:
            self.current_request['is_tracked'] = True
            self.current_request['request_track_object'] = RequestTrack.objects.create()

    def http_method_not_allowed(self, request, *args, **kwargs):
        self.current_request['status_code'] = status.HTTP_405_METHOD_NOT_ALLOWED
        self.response['allowed_methods'] = self.get_allowed_methods()
        return super().http_method_not_allowed(request, *args, **kwargs)

    def get_allowed_methods(self) -> List[str]:
        allowed = []
        for method in ['get', 'post', 'put', 'delete']:
            if callable(getattr(self, method, False)):
                allowed.append(method)
        return allowed

    def dispatch(self, request, *args, **kwargs):
        if self.current_request['exception']:
            return

        try:
            if self.authenticate and not self.is_authenticated():
                raise AuthException(AuthException.TOKEN_NOT_FOUND)
            self.current_request['view_start_time'] = datetime.datetime.now()
            result = super().dispatch(request, *args, **kwargs)
            self.current_request['view_end_time'] = datetime.datetime.now()

        except AvishanException as e:
            raise e
        except Exception as e:
            AvishanException(wrap_exception=e)
            raise e
        if current_request['exception']:
            return
        return result

    def is_authenticated(self) -> bool:
        """
        Checks for user available in current_request storage
        :return: true if authenticated
        """
        if not self.current_request['authentication_object']:
            return False
        return True

    def cast_data(self, key, value):
        if key in self.class_attributes_type.keys():
            if isinstance(self.class_attributes_type[key], type):
                return self.class_attributes_type[key](value)
            return self.class_attributes_type[key].__args__[0](value)
        return value


class AvishanApiView(AvishanView):
    is_api = True
    authenticate = True

    def dispatch(self, request, *args, **kwargs):
        if self.current_request['request'].method not in ['GET', 'DELETE']:
            try:
                if len(current_request['request'].body) > 0:
                    current_request['request'].data = json.loads(current_request['request'].body.decode('utf-8'))
                else:
                    current_request['request'].data = {}
            except:
                current_request['request'].data = {}

        super().dispatch(request, *args, **kwargs)
        return JsonResponse(self.response)


class AvishanTemplateView(AvishanView):
    is_api = False
    template_file_address: str = None
    template_url: str = None
    context: dict = {}

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.context = {
            **self.context,
            **{
                'CURRENT_REQUEST': self.current_request,
                'AVISHAN_CONFIG': get_avishan_config(),
                'self': self
            }
        }

    def dispatch(self, request, *args, **kwargs):
        self.parse_request_post_to_data()

        return super().dispatch(request, *args, **kwargs)

    def parse_request_post_to_data(self):
        if self.current_request['request'].method in ['POST', 'PUT']:
            try:
                if len(self.current_request['request'].body) > 0:
                    self.current_request['request'].data = dict(self.current_request['request'].POST)
                    for key, value in self.current_request['request'].data.items():
                        if len(value) == 1:
                            self.current_request['request'].data[key] = value[0]
                else:
                    self.current_request['request'].data = {}
            except:
                self.current_request['request'].data = {}

    def render(self):
        from django.shortcuts import render as django_render
        return django_render(self.request, self.template_file_address, self.context)


class AvishanModelApiView(AvishanApiView):
    authenticate = True
    track_it = True
    model: Type[AvishanModel] = None
    model_item: AvishanModel = None
    model_function: Callable = None  # todo these sends model not dict
    model_function_name: str = None
    direct_callable: Optional[DirectCallable] = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        model_plural_name = kwargs.get('model_plural_name', None)
        model_item_id = kwargs.get('model_item_id', None)
        self.model_function_name = kwargs.get('model_function_name', None)
        self.model = AvishanModel.get_model_by_plural_snake_case_name(model_plural_name)
        if not self.model:
            raise ErrorMessageException('Entered model name not found')

        if self.model_function_name is None:
            if request.method == 'GET':
                if model_item_id is None:
                    self.model_function_name = 'all'
                else:
                    self.model_function_name = 'get'
            elif request.method == 'POST':
                self.model_function_name = 'create'
            elif request.method == 'PUT':
                self.model_function_name = 'update'
            elif request.method == 'DELETE':
                self.model_function_name = 'remove'

        if model_item_id is not None:
            self.model_item = self.model.get(avishan_raise_400=True, id=int(model_item_id))
        if self.model_function_name is not None:
            for direct_callable in self.model.direct_callable_methods():
                if self.model_function_name == direct_callable.name:
                    self.direct_callable = direct_callable
                    break
            if not self.direct_callable:
                raise AuthException(AuthException.METHOD_NOT_DIRECT_CALLABLE)
            self.authenticate = self.direct_callable.authenticate
            try:
                if self.model_item is None:
                    self.model_function = getattr(self.model, self.model_function_name)
                else:
                    self.model_function = getattr(self.model_item, self.model_function_name)
            except AttributeError:
                raise ErrorMessageException(AvishanTranslatable(
                    EN=f'Requested method not found in model {self.model.class_name()}'
                ))

    @staticmethod
    def parse_returned_data(returned):
        if isinstance(returned, QuerySet):
            return [item.to_dict() for item in returned]
        elif isinstance(returned, list):
            if len(returned) > 0 and isinstance(returned[0], AvishanModel):
                return [item.to_dict() for item in returned]
            return returned
        elif isinstance(returned, AvishanModel):
            return returned.to_dict()
        else:
            return returned

    def get(self, request, *args, **kwargs):
        if self.model_function_name == 'get':
            result = self.model_item
        else:
            result = self.model_function()
        self.response[self.direct_callable.response_json_key] = self.parse_returned_data(result)

    def post(self, request, *args, **kwargs):
        if self.direct_callable.dismiss_request_json_key:
            data = request.data
        else:
            data = request.data[self.direct_callable.request_json_key]
        result = self.model_function(**data)
        self.response[self.direct_callable.response_json_key] = self.parse_returned_data(result)

    def put(self, request, *args, **kwargs):
        if self.direct_callable.dismiss_request_json_key:
            data = request.data
        else:
            data = request.data[self.direct_callable.request_json_key]
        result = self.model_function(**data)
        self.response[self.direct_callable.response_json_key] = self.parse_returned_data(result)

    def delete(self, request, *args, **kwargs):
        result = self.model_function()
        self.response[self.direct_callable.response_json_key] = self.parse_returned_data(result)


class PasswordHash(AvishanApiView):
    authenticate = False

    def get(self, request, *args, **kwargs):
        import bcrypt
        current_request['response']['hashed'] = bcrypt.hashpw(kwargs['password'].encode('utf8'),
                                                              bcrypt.gensalt()).decode('utf8')
        return JsonResponse(current_request['response'])
