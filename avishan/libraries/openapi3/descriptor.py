from typing import List, Union, Tuple

import yaml
from django.db.models.base import ModelBase
from django.utils import timezone

from avishan.configure import get_avishan_config

from avishan.descriptor import Project, DjangoAvishanModel, DirectCallable, RequestBodyDocumentation, \
    ResponseBodyDocumentation, Attribute, FunctionAttribute


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
        self.project = Project(name=get_avishan_config().PROJECT_NAME)
        self.models: List[DjangoAvishanModel] = sorted(self.project.models_pool(), key=lambda x: x.name)

    def export(self) -> dict:
        data = {
            'openapi': '3.0.1',
            'info': self._export_info(),
            'servers': self._export_servers(),
            'tags': self._export_tags(),
            'paths': self._export_paths(),
            # 'components': self._export_components()
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
        total = []
        for model in self.models:
            if model.is_abstract() or model.name in get_avishan_config().get_openapi_ignored_path_models():
                continue
            data = {'name': model.name}
            if model.description:
                data['description'] = model.description
            total.append(data)
        return total

    def _export_paths(self) -> dict:
        data = {}

        for model in self.models:
            if model.name in get_avishan_config().get_openapi_ignored_path_models():
                continue
            for direct_callable in model.direct_callables:
                direct_callable: DirectCallable
                if direct_callable.hide_in_redoc:
                    continue
                if direct_callable.url not in data.keys():
                    data[direct_callable.url] = Path(url=direct_callable.url)
                setattr(data[direct_callable.url], direct_callable.method.name.lower(), Operation(direct_callable))

        for key, value in data.items():
            data[key] = value.export()

        return data

    def export_yaml(self) -> str:
        return yaml.dump(self.export())


class Server:
    def __init__(self, url: str, description: str = None):
        self.url = url
        self.description = description


class Property:

    def __init__(self, name: str, schema: 'Schema', required: bool = True, default=Attribute.NO_DEFAULT):
        self.name = name
        self.schema = schema
        self.required = required
        self.default = default

    @classmethod
    def create_from_attribute(cls, attribute: Attribute, request_body_related: bool = False) -> 'Property':
        required = True
        if isinstance(attribute, FunctionAttribute):
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
    def __init__(self, request_body_documentation: RequestBodyDocumentation):
        self.content = Content.create_from_attribute(attribute=request_body_documentation.type_of)
        self.description = request_body_documentation.description
        self.required = True

    def export(self) -> dict:
        data = {
            'content': self.content.export(),
            'required': self.required
        }
        if self.description:
            data['description'] = self.description
        return data


class Response:
    def __init__(self, response_body_documentation: ResponseBodyDocumentation):
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
    def __init__(self, direct_callable: DirectCallable):
        self.direct_callable: DirectCallable = direct_callable
        self.tags: List[str] = [self.direct_callable.model.class_name()]
        self.summary: str = self.direct_callable.documentation.title
        self.description: str = self.direct_callable.documentation.description
        self.request_body: RequestBody = RequestBody(self.direct_callable.documentation.request_body)
        # self.responses: List[Response] = [Response(item) for item in self.direct_callable.documentation.response_bodies]

    def export(self) -> dict:
        data = {}
        if len(self.tags) > 0:
            data['tags'] = [item for item in self.tags]
        if self.summary:
            data['summary'] = self.summary
        if self.description:
            data['description'] = self.description
        if self.request_body:
            data['requestBody'] = self.request_body.export()
        # if len(self.responses) > 0:
        #     data['responses'] = {}
        #     for item in self.responses:
        #         data['responses'][str(item.status_code)] = item.export()

        return data


class Path:
    def __init__(self,
                 url: str,
                 get: Operation = None,
                 post: Operation = None,
                 put: Operation = None,
                 delete: Operation = None,
                 ):
        self.url = url
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

        return data
