from typing import Tuple, List, Optional, Union

import stringcase
import yaml
from django.db.models.base import ModelBase
from django.utils import timezone

from avishan.configure import get_avishan_config
from avishan.descriptor import Attribute, DirectCallable, FunctionAttribute, Project, DjangoAvishanModel


# todo tags
# todo POST body?
class OpenApi:

    def __init__(self):
        self.application_title = get_avishan_config().OPENAPI_APPLICATION_TITLE
        self.application_description = get_avishan_config().OPENAPI_APPLICATION_DESCRIPTION
        self.application_version = get_avishan_config().OPENAPI_APPLICATION_VERSION
        self.application_servers = get_avishan_config().OPENAPI_APPLICATION_SERVERS
        self.project: Project = get_avishan_config().PROJECT
        self.models: List[DjangoAvishanModel] = sorted(self.project.models_pool(), key=lambda x: x.name)

    def export(self) -> dict:
        # todo security
        data = {
            'openapi': '3.0.1',
            'info': self._export_info(),
            'servers': self._export_servers(),
            'tags': self._export_tags(),
            'x-tagGroups': self._export_tag_groups(),
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
        tags = []
        for item in self.models:
            if item.description:
                tags.append({
                    'name': stringcase.titlecase(item.name),
                    'description': item.description
                })
            else:
                tags.append({
                    'name': stringcase.titlecase(item.name)
                })
        return tags

    def _export_tag_groups(self):
        return [
            {
                'name': 'Models',
                'tags': [item['name'] for item in self._export_tags()]
            }
        ]

    def _export_paths(self) -> dict:
        data = {}
        for model in self.models:
            if model.name in get_avishan_config().get_openapi_ignored_path_models():
                continue
            for direct_callable in model.direct_callables:
                direct_callable: DirectCallable
                if direct_callable.hide_in_redoc or direct_callable.documentation is None:
                    continue
                if direct_callable.url not in data.keys():
                    data[direct_callable.url] = Path(url=direct_callable.url)

                setattr(data[direct_callable.url], direct_callable.method.name.lower(), Operation(
                    summary=direct_callable.documentation.title,
                    description=direct_callable.documentation.description,
                    request_body=Operation.extract_request_body_from_direct_callable(direct_callable),
                    responses=Operation.extract_responses_from_direct_callable(direct_callable),
                    tags=[stringcase.titlecase(model.name)]
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

    def __init__(self, name: str, schema: 'Schema', required: bool = True, default=Attribute.NO_DEFAULT):
        self.name = name
        self.schema = schema
        self.required = required
        self.default = default

    @classmethod
    def create_from_attribute(cls, attribute: Attribute, request_body_related: bool = False) -> 'Property':
        required = attribute.is_required
        created = Property(
            name=attribute.name,
            schema=Schema.create_from_attribute(attribute, request_body_related),
            required=required,
            default=attribute.default
        )
        created.schema.default = created.default
        return created

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
                 default=Attribute.NO_DEFAULT,
                 items: 'Schema' = None,
                 properties: List[Property] = None,
                 description: str = None,
                 enum: List[str] = None
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
        self.enum = enum

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
        if attribute.type is Attribute.TYPE.DATA_MODEL:
            return Schema(
                type='object',
                properties=[
                    Property(
                        name=item.name,
                        schema=Schema.create_from_attribute(item)
                    ) for item in attribute.type_of.attributes
                ]
            )

        create_kwargs = {
            'type': cls.type_exchange(attribute.type)[0],
            'format': cls.type_exchange(attribute.type)[1],
            'description': attribute.description,
            'enum': attribute.choices
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
    def create_from_model(cls, model: DjangoAvishanModel) -> 'Schema':
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
            'type': self.type,
            'description': ""
        }
        if self.type == 'integer':
            data['minimum'] = 1
            data['maximum'] = 9223372036854775807
        if self.format:
            data['format'] = self.format
        if self.default is not Attribute.NO_DEFAULT:
            data['default'] = self.default
        if self.description:
            data['description'] = self.description
        if self.items:
            data['items'] = self.items.export()
        if self.enum:
            enum = 'Enum: '
            for item in self.enum:
                enum += f"`{item}`, "
            data['description'] = enum[:-2] + "." + data['description']

        if len(data['description']) == 0:
            del data['description']

        if len(self.properties) > 0:
            data['properties'] = {}
            data['required'] = []
            for item in self.properties:
                if item.required:
                    data['required'].append(item.name)
                data['properties'][item.name] = item.export()
                if not item.required:
                    data['properties'][item.name]['nullable'] = True
            if len(data['required']) == 0:
                del data['required']

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

    @classmethod
    def create_from_attributes(cls, attributes: List[Attribute]):
        try:
            return Content(
                Schema(
                    type='object',
                    properties=[
                        Property(name=item.name, schema=Schema.create_from_attribute(item)) for item in attributes
                    ]
                )
            )
        except Exception as e:
            a = 1

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
    def __init__(self, content: Content, required: bool = True, examples=None):
        if examples is None:
            examples = []
        self.content = content
        self.required = required
        self.examples = examples

    def export(self) -> dict:
        data = {
            'content': self.content.export(),
            'required': self.required
        }
        if self.examples:
            data['content']['application/json']['examples'] = {}
            for example in self.examples:
                data['content']['application/json']['examples'][example.name] = {
                    "summary": example.summary,
                    "value": example.value
                }

        return data


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
                 tags: List[str] = None,
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
    def extract_request_body_from_direct_callable(direct_callable: DirectCallable) -> Optional[RequestBody]:
        if direct_callable.documentation.request_body is None:
            return None
        return RequestBody(
            content=Content(schema=Schema.create_object_from_args(
                direct_callable.documentation.request_body.attributes,
                request_body_related=True
            )),
            examples=direct_callable.documentation.request_body.examples,
        )

    @staticmethod
    def extract_responses_from_direct_callable(direct_callable: DirectCallable) -> List[Response]:
        responses = []
        for item in direct_callable.documentation.response_bodies:
            responses.append(Response(
                status_code=item.status_code,
                description=item.title,
                content=Content.create_from_attributes(item.attributes)
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
        if "{id}" in self.url:
            data['parameters'] = [{
                "name": "id",
                "in": "path",
                "required": True,
                "description": "Database specified id",
                "schema": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 9223372036854775807
                }
            }]
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
