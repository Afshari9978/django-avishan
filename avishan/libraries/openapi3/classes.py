from typing import List, Union, Type, Optional, Tuple

from django.db import models

from avishan.configure import get_avishan_config
from avishan.models import AvishanModel


class ApiDocumentation:
    paths: List['Path'] = []

    def add_get_path(self, url: str, summary: str = None, description: str = None, responses: List[
        'PathResponseGroup'] = ()):
        path = self.get_or_create_path(url)
        get_method = PathGetMethod()

    def add_post_path(self, url: str):
        pass

    def add_put_path(self, url: str):
        pass

    def add_delete_path(self, url: str):
        pass

    def get_or_create_path(self, url: str) -> 'Path':
        for path in self.paths:
            if path.url == url:
                return path
        return Path(url=url)


class SchemaProperty:
    def __init__(self, name: str, type: Union[str, 'Schema'], required: bool = False):
        self.name = name
        self.type = type
        self.required = required
        self.field: Optional[models.Field] = None

    @classmethod
    def create_from_model_field(cls, field: models.Field) -> 'SchemaProperty':
        schema_property = SchemaProperty(
            name=field.name,
            type=cls.get_type_from_field(field),
            required=AvishanModel.is_field_required(field)
        )
        schema_property.field = field
        return schema_property

    @staticmethod
    def get_type_from_field(field: models.Field) -> Union[str, 'Schema']:
        if isinstance(field, models.BooleanField):
            return "boolean"
        if isinstance(field, (models.IntegerField, models.AutoField)):
            return "number"
        if isinstance(field, models.FloatField):
            return "float"
        if isinstance(field, (models.CharField, models.TextField)):
            return "string"
        if isinstance(field, models.DateTimeField):
            return "date-time"
        if isinstance(field, models.DateField):
            return "date"
        if isinstance(field, models.TimeField):
            return "string"
        if isinstance(field, (models.OneToOneField, models.ForeignKey)):
            return Schema.create_from_model(field.related_model)
        if isinstance(field, models.FileField):
            return "string"
        raise NotImplementedError()

    def export_json(self):
        if isinstance(self.type, SchemaProperty):
            return {
                '$ref': f"#/components/schemas/{self.type.name}"
            }
        return {
            'type': self.type
        }

    def __str__(self):
        return self.name


class Schema:
    def __init__(self, name: str, type: str = 'object', properties: List[SchemaProperty] = ()):
        self.name = name
        self.type = type
        self.properties = properties
        self.model: Optional[AvishanModel] = None

    @classmethod
    def create_from_model(cls, model: Type[AvishanModel]):
        schema = Schema(name=model.class_name(), type="object", properties=cls.create_model_properties(model))
        schema.model = model
        return schema

    @classmethod
    def create_model_properties(cls, model: Type[AvishanModel]) -> List[SchemaProperty]:
        return [SchemaProperty.create_from_model_field(field) for field in model.get_fields()]

    def export_json(self) -> dict:
        return {
            "type": self.type,
            "properties": self.export_properties_json(),
            "required": self.export_required_json()
        }

    def export_required_json(self) -> List[str]:
        return [item.name for item in self.properties if item.required]

    def export_properties_json(self) -> dict:
        data = {}
        for prop in self.properties:
            data[prop.name] = prop.export_json()
        return data

    def __str__(self):
        return self.name


class Component:
    def __init__(self, schemas: List[Schema]):
        self.schemas = schemas

    def export_json(self):
        pass  # todo


class Content:
    def __init__(self, schema: Schema, type: str):
        self.schema = schema
        self.type = type

    def export_json(self) -> dict:
        return {
            'schema': self.schema.export_json()
        }


class Parameter:
    def __init__(self, name: str, schema: Schema, where: str = 'query', description: str = None, required: bool = False,
                 style: str = None):
        self.name = name
        self.schema = schema
        self.where = where
        self.description = description
        self.required = required
        self.style = style

    def export_json(self):
        pass  # todo


class PathRequest:
    def __init__(self, required: bool = True, contents: List[Content] = ()):
        self.required = required
        self.contents = contents

    def export_json(self) -> dict:
        data = {
            'required': self.required,
        }
        if len(self.contents) > 0:
            data['content'] = {}
        for content in self.contents:
            data['content'][content.type] = content.export_json()
        return data


class PathResponse:
    def __init__(self):
        pass


class PathResponseGroup:
    def __init__(self):
        pass

    def export_json(self) -> dict:
        pass


class PathMethod:
    method = None

    def __init__(self, summary: str = None, description: str = None, request: PathRequest = None,
                 responses: List[PathResponseGroup] = None, tags: List[str] = ()):
        self.request = request
        if responses is not None and len(responses) == 0:
            self.responses = None
        else:
            self.responses = responses

        self.tags = tags
        self.summary = summary
        self.description = description

    def export_json(self) -> dict:
        # todo added parameters
        data = {}
        if self.request:
            data['requestBody'] = self.request.export_json()
        if self.responses:
            data['responses'] = {}
            for response in self.responses.responses:
                data['responses'][response.status_code] = response.export_json()
        if len(self.tags) > 0:
            data['tags'] = self.tags
        if self.summary:
            data['summary'] = self.summary
        if self.description:
            data['description'] = self.description
        return data


class PathGetMethod(PathMethod):
    method = 'get'

    def __init__(self, summary: str = None, description: str = None,
                 responses: PathResponseGroup = None, tags: List[str] = ()):
        super().__init__(summary, description, None, responses, tags)


class PathPostMethod(PathMethod):
    method = 'post'


class PathPutMethod(PathMethod):
    method = 'put'


class PathDeleteMethod(PathMethod):
    method = 'delete'

    def __init__(self, summary: str = None, description: str = None,
                 responses: List[PathResponseGroup] = None, tags: List[str] = ()):
        super().__init__(summary, description, None, responses, tags)


class Path:
    def __init__(self, url: str, methods: List[PathMethod] = (), description: str = "", parameters: list = None):
        self.methods = methods
        self.url = url
        self.description = description
        self.parameters = OpenApi.request_common_url_parameters()
        if parameters:
            parameters.extend(parameters)

    def export_json(self):
        data = {}
        for path_method in self.methods:
            data[path_method.method] = path_method.export_json()

        return data


class OpenApi:
    def __init__(self, api_version: str, api_title: str, open_api_version: str = "3.0.0", api_description: str = None,
                 servers: Tuple[str] = ()):
        self.api_version = api_version
        self.api_title = api_title
        self.api_description = api_description
        self.servers = servers
        self.open_api_version = open_api_version
        self.models: List[Type[AvishanModel]] = []
        self.schemas = self.create_schemas_from_models()
        self.paths = self.create_paths_from_views()
        # todo security

    @staticmethod
    def request_common_url_parameters() -> List[dict]:
        # todo load from dict
        return get_avishan_config().REQUEST_COMMON_URL_PARAMETERS

    def create_schemas_from_models(self) -> List['Schema']:
        schemas = []
        for model in AvishanModel.__subclasses__():
            model: Type[AvishanModel]
            self.models.append(model)
            schemas.append(Schema.create_from_model(model))
        return schemas

    def create_paths_from_views(self) -> List['Path']:
        pass  # todo

    def export_schemas_json(self) -> dict:
        data = {}
        for schema in self.schemas:
            data[schema.name] = schema.export_json()
        return data

    def export_json(self) -> dict:
        # todo tags
        """
        "tags": [
            {
              "name": "pet",
              "description": "Everything about your Pets",
              "externalDocs": {
                "description": "Find out more",
                "url": "http://swagger.io"
              }
            },
            {
              "name": "store",
              "description": "Access to Petstore orders"
            },
            {
              "name": "user",
              "description": "Operations about user",
              "externalDocs": {
                "description": "Find out more about our store",
                "url": "http://swagger.io"
              }
            }
          ]
        """
        data = {
            'openapi': self.open_api_version,
            'info': {
                'version': self.api_version,
                'title': self.api_title
            },
            'components': {
                'schemas': self.export_schemas_json()
            },
            'paths': {}
        }
        if self.api_description:
            data['info']['description'] = self.api_description
        if len(self.servers) > 0:
            data['servers'] = [{'url': item} for item in self.servers]
        return data
