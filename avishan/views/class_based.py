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

            if self.track_it:
                self.current_request['request_track_object'].create_exec_infos(
                    self.current_request['request_track_exec'])
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

    @staticmethod
    def documentation() -> Optional[ApiDocumentation]:
        return None


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

    @staticmethod
    def documentation() -> Optional[ApiDocumentation]:
        # todo remove private fields from responses
        doc = ApiDocumentation()
        for model in AvishanModel.get_non_abstract_models():
            model_create = getattr(model, 'create')
            model_update = getattr(model, 'update')
            if len(dict(inspect.signature(model_create).parameters.items()).keys()) == 1 and \
                    list(dict(inspect.signature(model_create).parameters.items()).keys())[0] == 'kwargs':
                model_create_schema = Schema(
                    name=model.class_name()
                )
            else:
                model_create_schema = Schema.create_from_function(model.class_name(), model_create)
            if len(dict(inspect.signature(model_update).parameters.items()).keys()) == 2 and \
                    list(dict(inspect.signature(model_update).parameters.items()).keys())[1] == 'kwargs' and \
                    list(dict(inspect.signature(model_update).parameters.items()).keys())[0] == 'self':
                model_update_schema = Schema(
                    name=model.class_name()
                )
            else:
                model_update_schema = Schema.create_from_function(model.class_name(), model_update)

            doc.paths.append(
                Path(
                    url=f'{get_avishan_config().AVISHAN_URLS_START}/{model.class_plural_snake_case_name()}',
                    methods=[
                        PathGetMethod(
                            responses=PathResponseGroup(
                                responses=[
                                    PathResponse(
                                        status_code=200,
                                        contents=[Content(
                                            schema=Schema.schema_in_json(
                                                schema=Schema(
                                                    name=model.class_name(),
                                                    type='array',
                                                    items=Schema(name=model.class_name())),
                                                name=model.class_name()
                                            ),
                                            type='application/json'
                                        )],
                                        description='Get list of all items'
                                    )
                                ]
                            )
                        ),
                        PathPostMethod(
                            responses=PathResponseGroup(
                                responses=[
                                    PathResponse(
                                        status_code=200,
                                        contents=[Content(
                                            schema=Schema.schema_in_json(
                                                name=model.class_name(),
                                                schema=Schema.create_from_model(
                                                    model
                                                )
                                            ),
                                            type='application/json'
                                        )]
                                    )
                                ]
                            ),
                            request=PathRequest(
                                contents=[
                                    Content(
                                        schema=model_create_schema,
                                        type='application/json'
                                    )
                                ]
                            )
                        )
                    ]
                )
            )
            doc.paths.append(Path(
                url=f'{get_avishan_config().AVISHAN_URLS_START}/{model.class_plural_snake_case_name()}/'
                    + "{item_id}",
                methods=[
                    PathGetMethod(
                        responses=PathResponseGroup(
                            responses=[
                                PathResponse(
                                    status_code=200,
                                    contents=[Content(
                                        schema=Schema.schema_in_json(
                                            name=model.class_name(),
                                            schema=Schema.create_from_model(
                                                model
                                            )
                                        ),
                                        type='application/json'
                                    )],
                                    description='Get item'
                                )
                            ]
                        )
                    ),
                    PathPutMethod(
                        responses=PathResponseGroup(
                            responses=[
                                PathResponse(
                                    status_code=200,
                                    contents=[Content(
                                        schema=Schema.schema_in_json(
                                            name=model.class_name(),
                                            schema=Schema.create_from_model(
                                                model
                                            )
                                        ),
                                        type='application/json'
                                    )]
                                )
                            ]
                        ),
                        request=PathRequest(
                            contents=[
                                Content(
                                    schema=model_update_schema,
                                    type='application/json'
                                )
                            ]
                        )
                    ),
                    PathDeleteMethod(
                        responses=PathResponseGroup(
                            responses=[
                                PathResponse(
                                    status_code=200,
                                    contents=[Content(
                                        schema=Schema.schema_in_json(
                                            name=model.class_name(),
                                            schema=Schema.create_from_model(
                                                model
                                            )
                                        ),
                                        type='application/json'
                                    )],
                                    description='Delete item'
                                )
                            ]
                        )
                    )
                ]
            )
            )
            # todo custom function
            # for method in model.direct_callable_methods():
            #     method = getattr(model, method)
            #     method_name = method.__name__
            #     method_signature = dict(inspect.signature(method).parameters.items())
            #     method_return = inspect.signature(method).return_annotation
            #     if inspect.isclass(method_return) and issubclass(method_return, AvishanModel):
            #         method_response_schema = Schema.schema_in_json(
            #             name=model.class_name(),
            #             schema=Schema.create_from_model(
            #                 method_return
            #             )
            #         )
            #
            #     method_response_schema = None  # todo force for return type
            #     method_request_schema = None
            #
            #     if inspect.ismethod(method) and method.__self__ is model:
            #         # class method
            #         a = 1
            #
            #     else:
            #         # object method
            #         if len(method_signature.keys()) == 1 and list(method_signature.keys())[0] == 'self':
            #             method_method = 'get'
            #         else:
            #             method_method = 'post'
            #         a = 1

        return doc

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        model_plural_name = kwargs.get('model_plural_name', None)
        model_item_id = kwargs.get('model_item_id', None)
        model_function_name = kwargs.get('model_function_name', None)
        self.model = AvishanModel.get_model_by_plural_snake_case_name(model_plural_name)
        if not self.model:
            raise ErrorMessageException('Entered model name not found')

        if model_item_id is not None:
            self.model_item = self.model.get(avishan_raise_400=True, id=int(model_item_id))
        if model_function_name is not None:
            if model_function_name not in \
                    self.model.direct_callable_methods() + self.model.direct_non_authenticated_callable_methods():
                raise AuthException(AuthException.METHOD_NOT_DIRECT_CALLABLE)
            if model_function_name in self.model.direct_non_authenticated_callable_methods():
                self.authenticate = False
            try:
                if self.model_item is None:
                    self.model_function = getattr(self.model, model_function_name)
                else:
                    self.model_function = getattr(self.model_item, model_function_name)
            except AttributeError:
                raise ErrorMessageException(AvishanTranslatable(
                    EN=f'Requested method not found in model {self.model.class_name()}'
                ))
            # todo have check on callables from model

    def parse_returned_data(self, returned):
        if isinstance(returned, QuerySet):
            returned = [item.to_dict() for item in returned]
            self.response[self.model.class_plural_snake_case_name()] = returned
        elif isinstance(returned, list):
            if len(returned) > 0 and isinstance(returned[0], AvishanModel):
                returned = [item.to_dict() for item in returned]
            self.response[self.model.class_plural_snake_case_name()] = returned
        elif isinstance(returned, AvishanModel):
            self.response[self.model.class_snake_case_name()] = returned.to_dict()
        else:
            self.response[self.model.class_plural_snake_case_name()] = returned

    def get(self, request, *args, **kwargs):
        if self.model_function is None:
            if self.model_item is None:
                self.response[self.model.class_plural_snake_case_name()] = [item.to_dict() for item in
                                                                            self.model.all()]
            else:
                self.response[self.model.class_snake_case_name()] = self.model_item.to_dict()
        else:
            self.parse_returned_data(self.model_function())

    def post(self, request, *args, **kwargs):
        if self.model_function is None:
            data = request.data[self.model.class_snake_case_name()]
            self.response[self.model.class_snake_case_name()] = self.model.create(**data).to_dict()
        else:
            data = request.data
            self.parse_returned_data(self.model_function(**data))

    def put(self, request, *args, **kwargs):

        request_data = request.data[self.model.class_snake_case_name()].copy()

        self.response[self.model.class_snake_case_name()] = self.model_item.update(**request_data).to_dict()

    def delete(self, request, *args, **kwargs):
        self.response[self.model.class_snake_case_name()] = self.model_item.remove()


class PasswordHash(AvishanApiView):
    authenticate = False

    def get(self, request, *args, **kwargs):
        import bcrypt
        current_request['response']['hashed'] = bcrypt.hashpw(kwargs['password'].encode('utf8'),
                                                              bcrypt.gensalt()).decode('utf8')
        return JsonResponse(current_request['response'])
