import typing

from django.db import models

from avishan.configure import get_avishan_config

from inspect import Parameter as InspectParameter

from avishan.models import AvishanModel


class ApiDocumentation:
    paths: typing.List['Path'] = []

    def get_or_create_path(self, url: str) -> 'Path':
        for path in self.paths:
            if path.url == url:
                return path
        return Path(url=url)


# todo example for data
def type_map(input: typing.Union[str, type, models.Field], name: str = None, model=None) -> typing.Tuple[
    typing.Union[str, 'Schema'], typing.Optional[str]]:
    if isinstance(input, str):
        return input, None
    if isinstance(input, Schema):
        return input, None
    if isinstance(input, models.Field):
        if isinstance(input, models.BooleanField):
            return "boolean", None
        if isinstance(input, (models.IntegerField, models.AutoField)):
            return "number", "int64"
        if isinstance(input, models.FloatField):
            return "number", "float"
        if isinstance(input, (models.CharField, models.TextField)):
            return "string", None
        if isinstance(input, models.DateTimeField):
            return "string", "date-time"
        if isinstance(input, models.DateField):
            return "string", "full-date"
        if isinstance(input, models.TimeField):
            return "string", 'full-time'
        if isinstance(input, (models.OneToOneField, models.ForeignKey)):
            if input.model.__name__ is model.model.__name__:
                return model, None
            return Schema.create_from_model(input.related_model), None
        if isinstance(input, models.FileField):
            return "string", None
        raise NotImplementedError(name)
    if isinstance(input, type):
        if input is str:
            return 'string', None
        if input is bool:
            return 'boolean', None
        if input is int:
            return 'number', 'int64'
        if input is float:
            return 'number', 'float'
        raise NotImplementedError(name)

    # Optional[int] -> Union[int, None]
    # noinspection PyUnresolvedReferences
    if isinstance(input, typing._Union) and len(input.__args__) == 2:
        # noinspection PyUnresolvedReferences
        return type_map(input.__args__[0], name=name)

    raise NotImplementedError(name)


class SchemaProperty:
    def __init__(self, name: str, type: typing.Union[str, type, models.Field, 'Schema'], required: bool = False,
                 raw: bool = False, model=None):
        self.name = name
        self.type, self.format = type_map(type, name, model=model)
        self.required = required
        self.field: typing.Optional[models.Field] = None
        self.raw = raw

    @classmethod
    def create_from_model_field(cls, field: models.Field, model=None) -> 'SchemaProperty':
        schema_property = SchemaProperty(
            name=field.name,
            type=field,
            required=AvishanModel.is_field_required(field),
            model=model
        )
        schema_property.field = field
        return schema_property

    def export_json(self):
        if self.raw:
            return self.type.export_json()
        if not isinstance(self.type, str):
            return {
                '$ref': f"#/components/schemas/{self.type.name}"
            }
        return {
            'type': self.type
        }

    def __str__(self):
        return self.name


class Schema:
    created = {}

    def __init__(self, name: str, type: str = 'object', properties: typing.List[SchemaProperty] = (),
                 items: 'Schema' = None,
                 raw: bool = False):
        self.name = name
        self.type = type
        self.properties = properties
        self.items: typing.Optional[Schema] = items
        self.model: typing.Optional[AvishanModel] = None
        self.raw = raw
        if self.raw:
            for prop in self.properties:
                prop.raw = True

    @classmethod
    def create_from_model(cls, model: typing.Type[AvishanModel]):
        if model not in cls.created.keys():
            schema = Schema(name=model.class_name(), type="object")
            schema.model = model
            schema.properties = schema.create_model_properties(model)
            cls.created[model] = schema
        else:
            schema = cls.created[model]
        return schema

    def create_model_properties(self, model: typing.Type[AvishanModel]) -> typing.List[SchemaProperty]:
        return [SchemaProperty.create_from_model_field(field, model=self) for field in model.get_fields()]

    @classmethod
    def create_from_function(cls, name: str, function):
        import inspect

        properties = []
        for key, value in dict(inspect.signature(function).parameters.items()).items():
            value: InspectParameter
            if key in ['self', 'cls', 'kwargs']:
                continue
            # noinspection PyUnresolvedReferences
            if type(value.annotation) is inspect._empty:
                raise ValueError(f'Method ({function}) parameter ({key}) type not defined')
            if inspect.isclass(value.annotation) and issubclass(value.annotation, AvishanModel):
                param_type = Schema.create_from_model(value.annotation)
            else:
                try:
                    param_type = Schema.create_from_model(value.annotation.__args__[0])
                except:
                    param_type = value.annotation

            properties.append(SchemaProperty(
                name=key,
                type=param_type,
                required=True  # todo check
            ))

        return cls(
            name=name,
            type='object',
            properties=properties
        )

    def export_json(self) -> dict:
        return {
            "type": self.type,
            "properties": self.export_properties_json(),
            "required": self.export_required_json()
        } if self.items is None else {
            'type': self.type,
            'items': self.items.export_json()
        }

    def export_reference(self) -> dict:
        if self.raw:
            return self.export_json()
        return {
            "$ref": f"#/components/schemas/{self.name}"
        } if self.items is None else {
            'type': self.type,
            'items': self.items.export_reference()
        }

    def export_required_json(self) -> typing.List[str]:
        return [item.name for item in self.properties if item.required]

    def export_properties_json(self) -> dict:
        data = {}
        for prop in self.properties:
            data[prop.name] = prop.export_json()
        return data

    @classmethod
    def schema_in_json(cls, name: str, schema: 'Schema'):
        return Schema(
            name=name,
            type='object',
            properties=[SchemaProperty(
                name=name,
                type=schema
            )]
        )

    @classmethod
    def raw_schema_from_dict(cls, data: dict) -> typing.Union['Schema', 'SchemaProperty']:
        import inspect

        name = list(data.keys())[0]
        properties = []
        items = None
        if isinstance(data[name], dict):
            type = 'object'
            for key, value in data[name].items():
                if isinstance(value, dict):
                    inner_type = SchemaProperty(
                        name=key,
                        type=Schema.raw_schema_from_dict(
                            {key: value}
                        )
                    )
                elif isinstance(value, list):
                    inner_type = SchemaProperty(
                        name=key,
                        type=Schema.raw_schema_from_dict({
                            key: [value[0]]
                        })
                    )
                elif inspect.isclass(value) and issubclass(value, AvishanModel):
                    inner_type = SchemaProperty(
                        name=key,
                        type=Schema.create_from_model(
                            value
                        )
                    )
                else:
                    inner_type = SchemaProperty(
                        name=key,
                        type=value
                    )

                properties.append(
                    inner_type
                )
        elif isinstance(data[name], list):
            type = 'array'
            items = Schema(
                name=name,
                type='array',
                items=Schema.raw_schema_from_dict(data[name][0])
            )
        else:
            if issubclass(data[name], AvishanModel):
                return SchemaProperty(
                    name=name,
                    type=Schema.create_from_model(data[name])
                )
            return SchemaProperty(
                name=name,
                type=data[name]
            )
        return Schema(
            name=name,
            type=type,
            properties=properties,
            items=items
        )

    def __str__(self):
        return self.name


class Component:
    def __init__(self, schemas: typing.List[Schema]):
        self.schemas = schemas

    def export_json(self):
        data = {
            'schemas': {}
        }
        for schema in self.schemas:
            data['schemas'][schema.name] = schema.export_json()
        return data


class Content:
    def __init__(self, schema: Schema, type: str, raw: bool = False):
        self.schema = schema
        self.type = type
        self.raw = raw

    def export_json(self) -> dict:
        return {
            'schema': self.schema.export_reference()
        } if not self.raw else {
            'schema': self.schema.export_json()
        }


def __str__(self):
    return f'{self.schema}'


class ContentArray(Content):

    def __init__(self, schema: Schema, type: str):
        super().__init__(schema, type)


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

    def __str__(self):
        return self.name


class PathRequest:
    def __init__(self, required: bool = True, contents: typing.List[Content] = ()):
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

    def __str__(self):
        return f'{len(self.contents)} requests'


class PathResponse:
    def __init__(self, status_code: int, contents: typing.List[Content], description: str = None):
        self.status_code = status_code
        self.contents = contents
        self.description = description

    def export_json(self) -> dict:
        data = {}
        if len(self.contents) > 0:
            data['content'] = {}
        for content in self.contents:
            data['content'][content.type] = content.export_json()
        if self.description:
            data['description'] = self.description
        return data

    def __str__(self):
        return self.status_code


class PathResponseGroup:
    def __init__(self, responses: typing.List[PathResponse]):
        self.responses = responses

    def export_json(self) -> dict:
        data = {}
        for item in self.responses:
            data[item.status_code] = item.export_json()
        return data

    def __str__(self):
        return f'{len(self.responses)} responses'


class PathMethod:
    method = None

    def __init__(self, summary: str = None, description: str = None, request: PathRequest = None,
                 responses: PathResponseGroup = None, tags: typing.List[str] = ()):
        self.request = request
        if responses is not None and len(responses.responses) == 0:
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

    def __str__(self):
        return f'{self.method.upper()}'


class PathGetMethod(PathMethod):
    method = 'get'

    def __init__(self, summary: str = None, description: str = None,
                 responses: PathResponseGroup = None, tags: typing.List[str] = ()):
        super().__init__(summary, description, None, responses, tags)


class PathPostMethod(PathMethod):
    method = 'post'


class PathPutMethod(PathMethod):
    method = 'put'


class PathDeleteMethod(PathMethod):
    method = 'delete'

    def __init__(self, summary: str = None, description: str = None,
                 responses: PathResponseGroup = None, tags: typing.List[str] = ()):
        super().__init__(summary, description, None, responses, tags)


class Path:
    def __init__(self, url: str, methods: typing.List[PathMethod] = (), description: str = "", parameters: list = None):
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

    def __str__(self):
        return self.url


class OpenApi:
    def __init__(self, api_version: str, api_title: str, open_api_version: str = "3.0.0", api_description: str = None,
                 servers: typing.Tuple[str] = ()):
        self.api_version = api_version
        self.api_title = api_title
        self.api_description = api_description
        self.servers = servers
        self.open_api_version = open_api_version
        self.models: typing.List[typing.Type[AvishanModel]] = []
        self.schemas = self.create_schemas_from_models()
        self.paths = self.create_paths_from_views()

        # todo security

    @staticmethod
    def request_common_url_parameters() -> typing.List[dict]:
        # todo load from dict
        return get_avishan_config().REQUEST_COMMON_URL_PARAMETERS

    def create_schemas_from_models(self) -> typing.List['Schema']:
        def all_subclasses(cls):
            return set(cls.__subclasses__()).union(
                [s for c in cls.__subclasses__() for s in all_subclasses(c)])

        schemas = []
        for model in sorted(all_subclasses(AvishanModel), key=lambda x: x.class_name()):
            model: typing.Type[AvishanModel]
            self.models.append(model)
            schemas.append(Schema.create_from_model(model))
        return schemas

    @staticmethod
    def create_paths_from_views() -> typing.List['Path']:
        from avishan.views.class_based import AvishanModelApiView

        if AvishanModelApiView.documentation():
            return AvishanModelApiView.documentation().paths
        else:
            return []

    def export_schemas_json(self) -> dict:
        data = {}
        for schema in self.schemas:
            data[schema.name] = schema.export_json()
        return data

    def export_paths_json(self) -> dict:
        data = {}
        for path in self.paths:
            data[path.url] = path.export_json()
        return data

    def export_json(self) -> dict:
        # todo tags
        data = {
            'openapi': self.open_api_version,
            'info': {
                'version': self.api_version,
                'title': self.api_title
            },
            'components': {
                'schemas': self.export_schemas_json()
            },
            'paths': self.export_paths_json()
        }
        if self.api_description:
            data['info']['description'] = self.api_description
        if len(self.servers) > 0:
            data['servers'] = [{'url': item} for item in self.servers]
        return data
