from typing import List, Union, Type, Optional

from django.db import models

from avishan.configure import get_avishan_config
from avishan.models import AvishanModel


class OpenApi:
    def __init__(self, api_version: str, api_title: str, open_api_version: str = "3.0.0"):
        self.api_version = api_version
        self.api_title = api_title
        self.open_api_version = open_api_version
        self.models: List[Type[AvishanModel]] = []
        self.schemas = self.create_schemas()
        a = 1

    @staticmethod
    def request_common_url_parameters() -> List[dict]:
        return get_avishan_config().REQUEST_COMMON_URL_PARAMETERS

    def create_schemas(self) -> List['Schema']:
        schemas = []
        for model in AvishanModel.__subclasses__():
            model: Type[AvishanModel]
            self.models.append(model)
            schemas.append(Schema.create_from_model(model))
        return schemas

    def export_schemas_json(self) -> dict:
        data = {}
        for schema in self.schemas:
            data[schema.name] = schema.export_json()
        return data

    def export_json(self) -> dict:
        return {
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
