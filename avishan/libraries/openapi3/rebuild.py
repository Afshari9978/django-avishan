from typing import Tuple, List, Optional, Union

from django.db.models.base import ModelBase
from django.utils import timezone

from avishan.configure import get_avishan_config
from avishan.descriptor import Attribute, ApiMethod, Model, DjangoModel, DirectCallable


# todo tags
# todo POST body? 
class OpenApi:

    def __init__(self,
                 application_title: str,
                 application_description: str = None,
                 application_version: str = '0.1.0',
                 application_servers: List['Server'] = None
                 ):
        self.application_title = application_title
        self.application_description = application_description
        self.application_version = application_version
        self.application_servers = application_servers
        self.models: List[Model] = sorted(get_avishan_config().get_openapi_schema_models(), key=lambda x: x.name)

    def export(self) -> dict:
        # todo security
        data = {
            'openapi': '3.0.1',
            'info': self._export_info(),
            'servers': self._export_servers(),
            'tags': self._export_tags(),
            'paths': self._export_paths(),
            'components': self._export_components()
        }
        return data

    def _export_info(self):
        return {
            'title': self.application_title,
            'description': self.application_description,
            'version': self.application_version
        }

    def _export_servers(self):
        return [
            {
                'url': item.url,
                'description': item.description
            }
            for item in self.application_servers
        ]

    def _export_tags(self) -> list:
        # todo https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.0.md#tagObject
        return []

    def _export_paths(self) -> dict:
        data = {}
        for model in self.models:
            if model.name in get_avishan_config().get_openapi_ignored_path_models():
                continue
            for api_method in model.methods:
                api_method: DirectCallable
                if api_method.hide_in_redoc:
                    continue
                if api_method.url not in data.keys():
                    data[api_method.url] = Path(url=api_method.url)
                setattr(data[api_method.url], api_method.method.name.lower(), Operation(
                    summary=api_method.short_description,
                    description=api_method.long_description,
                    request_body=Operation.extract_request_body_from_api_method(api_method),
                    responses=Operation.extract_responses_from_api_method(api_method),
                ))

        for key, value in data.items():
            data[key] = value.export()

        return data

    def _export_components(self) -> dict:
        data = {
            'schemas': self._export_schemas(),
            'responses': self._export_responses(),
            'parameters': self._export_parameters(),
            'examples': self._export_examples(),
            'requestBodies': self._export_request_bodies(),
            'headers': self._export_headers(),
            'securitySchemes': self._export_securitySchemes(),
        }
        delete_list = []
        for key, value in data.items():
            if value == {}:
                delete_list.append(key)
        for item in delete_list:
            del data[item]
        return data

    def _export_schemas(self) -> dict:
        schemas = {}
        for model in self.models:
            schemas[model.name] = Schema.create_from_model(model).export()
        return schemas

    def _export_responses(self) -> dict:
        # todo
        return {}

    def _export_parameters(self) -> dict:
        # todo
        return {}

    def _export_examples(self) -> dict:
        # todo
        return {}

    def _export_request_bodies(self) -> dict:
        # todo
        return {}

    def _export_headers(self) -> dict:
        # todo
        return {}

    def _export_securitySchemes(self) -> dict:
        # todo
        return {}

    def export_yaml(self) -> str:
        import yaml
        return yaml.dump(self.export())


class Server:
    def __init__(self, url: str, description: str = None):
        self.url = url
        self.description = description


class Tag:

    def __init__(self, name: str):
        self.name = name


class Parameter:
    # todo
    pass


class Property:
    def __init__(self, name: str, schema: 'Schema'):
        self.name = name
        self.schema = schema

    @classmethod
    def create_from_attribute(cls, attribute: Attribute, request_body_related: bool = False) -> 'Property':
        return Property(
            name=attribute.name,
            schema=Schema.create_from_attribute(attribute, request_body_related)
        )

    def export(self) -> dict:
        return self.schema.export()


class Schema:
    _TYPE_POOL = {
        Attribute.TYPE.STRING: ('string', None),
        Attribute.TYPE.INT: ('integer', None),
        Attribute.TYPE.FLOAT: ('number', 'float'),
        Attribute.TYPE.DATE: ('string', 'date'),
        Attribute.TYPE.TIME: ('string', 'time'),
        Attribute.TYPE.DATETIME: ('string', 'date-time'),
        Attribute.TYPE.BOOLEAN: ('boolean', None),
        Attribute.TYPE.ARRAY: ('array', None)
    }

    def __init__(self,
                 name: str = None,
                 type: str = None,
                 format: str = None,
                 default: str = None,
                 items: 'Schema' = None,
                 properties: List[Property] = None,
                 description: str = None
                 ):
        if properties is None:
            properties = []

        self.name = name
        self.type = type
        self.format = format
        self.default = default
        self.items = items
        self.properties = properties
        self.description = description

    @classmethod
    def create_from_attribute(cls, attribute: Attribute, request_body_related: bool = False) -> 'Schema':
        if attribute.type is Attribute.TYPE.OBJECT:
            if request_body_related:
                return Schema(
                    type='object',
                    properties=[
                        Property(name='id', schema=Schema(type='integer'))
                    ]
                )
            else:
                return Schema(name=attribute.type_of.__name__)
        if attribute.type is Attribute.TYPE.FILE:
            return Schema(name='File')

        create_kwargs = {
            'type': cls.type_exchange(attribute.type)[0],
            'format': cls.type_exchange(attribute.type)[1],
            'description': attribute.description
        }
        if attribute.type is Attribute.TYPE.ARRAY:
            create_kwargs['items'] = cls.type_exchange(attribute.type_of)
            if isinstance(create_kwargs['items'], tuple):
                create_kwargs['items'] = Schema(type=create_kwargs['items'][0])

        return Schema(**create_kwargs)

    @classmethod
    def create_object_from_args(cls, args: List[Attribute], request_body_related: bool = False) -> 'Schema':
        return Schema(
            type='object',
            properties=[Property.create_from_attribute(item, request_body_related) for item in args]
        )

    @classmethod
    def create_from_model(cls, model: DjangoModel) -> 'Schema':
        return cls.create_object_from_args(model.attributes)

    @classmethod
    def type_exchange(cls, entry: Union[Attribute.TYPE, ModelBase]) -> Union[Tuple[str, str], 'Schema']:
        try:
            return cls._TYPE_POOL[entry]
        except KeyError:
            if isinstance(entry, ModelBase):
                return Schema(name=entry.__name__)

        raise NotImplementedError()

    def export(self) -> dict:
        if self.name:
            return {
                "$ref": f"#/components/schemas/{self.name}"
            }
        data = {
            'type': self.type
        }
        if self.format:
            data['format'] = self.format
        if self.description:
            data['description'] = self.description
        if self.items:
            data['items'] = self.items.export()

        if len(self.properties) > 0:
            data['properties'] = {}
            for item in self.properties:
                data['properties'][item.name] = item.export()

        if self.type == 'string' and self.format == 'date-time':
            data['example'] = timezone.now().strftime(get_avishan_config().DATETIME_STRING_FORMAT)
        if self.type == 'string' and self.format == 'date':
            data['example'] = timezone.now().strftime(get_avishan_config().DATE_STRING_FORMAT)

        return data


class Content:
    def __init__(self, schema: Schema, examples=None):
        self.schema = schema
        self.examples = examples  # todo

    @classmethod
    def create_from_attribute(cls, attribute: Attribute) -> 'Content':
        return Content(
            Schema.create_from_attribute(attribute)
        )

    def export(self) -> dict:
        data = {
            "application/json": {
                "schema": self.schema.export()
            }
        }
        if self.examples:
            data['application/json']['examples'] = self.examples
        return data


class RequestBody:
    def __init__(self, content: Content, required: bool = True):
        self.content = content
        self.required = required

    def export(self) -> dict:
        return {
            'content': self.content.export(),
            'required': self.required
        }


class Response:
    def __init__(self, status_code: int, description: str = None, content: Content = None):
        self.status_code = status_code
        self.description = description
        self.content = content

    def export(self) -> dict:
        data = {}
        if self.description:
            data['description'] = self.description
        if self.content:
            data['content'] = self.content.export()
        return data


class Operation:
    def __init__(self,
                 tags: List[Tag] = None,
                 summary: str = None,
                 description: str = None,
                 parameters: List[Parameter] = None,
                 request_body: RequestBody = None,
                 responses: List[Response] = None
                 ):
        if tags is None:
            tags = []
        if parameters is None:
            parameters = []
        if responses is None:
            responses = []

        self.tags = tags
        self.summary = summary
        self.description = description
        self.parameters = parameters
        self.request_body = request_body
        self.responses = responses

    @staticmethod
    def extract_request_body_from_api_method(api_method: DirectCallable) -> Optional[RequestBody]:
        if len(api_method.args) == 0:
            return None
        content = Content(schema=Schema.create_object_from_args(api_method.args, request_body_related=True))
        if not api_method.dismiss_request_json_key:
            content.schema = Schema(
                type='object',
                properties=[Property(
                    name=api_method.request_json_key,
                    schema=content.schema
                )]
            )
        return RequestBody(content=content)

    @staticmethod
    def extract_responses_from_api_method(api_method: DirectCallable) -> List[Response]:
        responses = []
        for item in api_method.responses:
            content = Content.create_from_attribute(item.returns)
            if not api_method.dismiss_response_json_key:
                content.schema = Schema(
                    type='object',
                    properties=[Property(
                        name=api_method.response_json_key,
                        schema=content.schema
                    )]
                )
            responses.append(Response(
                status_code=item.status_code,
                description=item.description,
                content=content
            ))

        return responses

    def export(self) -> dict:
        data = {}
        if len(self.tags) > 0:
            data['tags'] = [item for item in self.tags]
        if self.summary:
            data['summary'] = self.summary
        if self.description:
            data['description'] = self.description
        if len(self.parameters) > 0:
            raise NotImplementedError()
        if self.request_body:
            data['requestBody'] = self.request_body.export()
        if len(self.responses) > 0:
            data['responses'] = {}
            for item in self.responses:
                data['responses'][str(item.status_code)] = item.export()

        return data


class Path:
    def __init__(self,
                 url: str,
                 summary: str = None,
                 description: str = None,
                 get: Operation = None,
                 post: Operation = None,
                 put: Operation = None,
                 delete: Operation = None,
                 ):
        self.url = url
        self.summary = summary
        self.description = description
        self.get = get
        self.post = post
        self.put = put
        self.delete = delete

    def export(self) -> dict:
        data = {}
        if self.get:
            data['get'] = self.get.export()
        if self.post:
            data['post'] = self.post.export()
        if self.put:
            data['put'] = self.put.export()
        if self.delete:
            data['delete'] = self.delete.export()
        if self.description:
            data['description'] = self.description
        if self.summary:
            data['summary'] = self.summary

        return data
