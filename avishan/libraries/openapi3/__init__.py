import inspect
from inspect import Parameter
from typing import Type, List, Tuple, Dict

from django.db import models

from avishan.models import AvishanModel
import stringcase


def request_common_parameters() -> List[dict]:
    return [{
        "name": 'lang',
        "in": 'query',
        "description": 'set language for this request',
        "required": False,
    }]


def create_openapi_object(title: str, api_version: str, servers: List[dict] = None) -> dict:
    data = {
        'openapi': "3.0.0",
        'info': get_info_object(api_version, title),
        'servers': servers,
        'components': {
            'schemas': {}
        },
        'paths': {}
    }
    for model in AvishanModel.get_models():
        data['components']['schemas'][model.class_name()] = (get_model_object(model))
        data['paths'] = {**data['paths'], **get_model_paths(model)}
    return data


def get_info_object(api_version: str, title: str):
    # todo
    return {
        'version': api_version,
        'title': title
    }


def get_model_paths(model: Type[AvishanModel]) -> dict:
    data = {}
    data[f'/api/av1/{model.class_plural_snake_case_name()}'] = {
        "get": get_model_get_request(model),
        "post": get_model_post_request(model)
    }
    data[f'/api/av1/{model.class_plural_snake_case_name()}' + '/{item_id}'] = {
        "get": get_item_get_request(model),
        "put": get_item_put_request(model),
        "delete": get_item_delete_request(model),
    }
    for key, value in data.items():
        deletes = []

        for inner_key, inner_value in data[key].items():
            if inner_value == {}:
                deletes.append(inner_key)
        for item in deletes:
            del data[key][item]
    return data


def get_model_get_request(model: Type[AvishanModel]):
    return {
        "description": f"Get list of {stringcase.titlecase(model.class_name())}",
        "parameters": request_common_parameters(),
        "responses": {
            "200": {
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "array",
                            "items": {
                                "$ref": f"#/components/schemas/{model.class_name()}"
                            }
                        }
                    }
                },
                "description": "succeed"
            }
        }
    }


def get_model_post_request(model: Type[AvishanModel]) -> dict:
    if model.Meta.abstract is True:
        return {}
    create_schema = get_model_create_schema(model)
    if create_schema == {}:
        return {}
    return {
        "description": f"Create {stringcase.titlecase(model.class_name())}",
        "parameters": request_common_parameters(),
        "requestBody": {
            "description": "Data structure for creation",
            "content": {
                "application/json": {
                    "schema": create_schema
                }
            },
            "required": True
        },
        "responses": {
            "200": {
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "array",
                            "items": {
                                "$ref": f"#/components/schemas/{model.class_name()}"
                            }
                        }
                    }
                },
                "description": "succeed"
            }
        }
    }


def get_item_get_request(model: Type[AvishanModel]) -> dict:
    return {
        "description": f"Get item of {stringcase.titlecase(model.class_name())}",
        "parameters": request_common_parameters(),
        "responses": {
            "200": {
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                model.class_snake_case_name(): {
                                    "$ref": f"#/components/schemas/{model.class_name()}"
                                }
                            }
                        }
                    }
                },
                "description": "succeed"
            }
        }
    }


def get_item_put_request(model: Type[AvishanModel]) -> dict:
    if model.Meta.abstract is True:
        return {}
    update_schema = get_model_update_schema(model)
    if update_schema == {}:
        return {}
    return {
        "description": f"Update {stringcase.titlecase(model.class_name())} item",
        "parameters": request_common_parameters(),
        "requestBody": {
            "description": "Data structure for edit",
            "content": {
                "application/json": {
                    "schema": update_schema
                }
            },
            "required": True
        },
        "responses": {
            "200": {
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                model.class_snake_case_name(): {
                                    "$ref": f"#/components/schemas/{model.class_name()}"
                                }
                            }
                        }
                    }
                },
                "description": "succeed"
            }
        }
    }


def get_item_delete_request(model: Type[AvishanModel]) -> dict:
    if model.Meta.abstract is True:
        return {}
    return {
        "description": f"Delete item_id from {stringcase.titlecase(model.class_name())}",
        "parameters": request_common_parameters(),
        "responses": {
            "200": {
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                model.class_snake_case_name(): {
                                    "$ref": f"#/components/schemas/{model.class_name()}"
                                }
                            }
                        }
                    }
                },
                "description": "succeed"
            }
        }
    }


def get_functions_properties(function) -> Dict[str, Parameter]:
    return dict(inspect.signature(function).parameters.items())


def get_model_create_schema(model: Type[AvishanModel]) -> dict:
    data = {
        "type": "object",
        "properties": {}
    }
    create_function = getattr(model, 'create')
    for name, param in get_functions_properties(create_function):
        if name == 'kwargs':
            return {}
        data['properties'][name] = get_input_object(param)
    return data


def get_model_update_schema(model):
    import inspect
    data = {
        "type": "object",
        "properties": {}
    }
    update_function = getattr(model, 'update')

    update_signature = inspect.signature(update_function)
    for name, param in update_signature.parameters.items():
        if name == 'self':
            continue
        if name == 'kwargs':
            return {}
        data['properties'][name] = get_input_object(param)
    return data


def get_input_object(param: Parameter) -> dict:
    data = {
        'type': param.annotation,
        'default': param.default
    }
    if param.annotation is _empty:
        raise ValueError(f"Documentation Parse failed: {param}")
    if param.default is _empty:
        del data['default']

    if data['type'] == int:
        data['type'] = "integer"
    elif data['type'] == float:
        data['type'] = "float"
    elif data['type'] == str:
        data['type'] = "string"
    elif data['type'] == bool:
        data['type'] = 'boolean'
    elif inspect.isclass(data['type']) and issubclass(data['type'], AvishanModel):
        data = {
            "$ref": f"#/components/schemas/{data['type'].class_name()}"
        }
        return data
    else:
        try:
            data = {
                'type': "array",
                "items": {
                    "$ref": f"#/components/schemas/{data['type'].__args__[0].class_name()}"
                }
            }
        except:
            raise NotImplementedError()
    return data


def get_model_object(model: Type[AvishanModel]) -> dict:
    return {
        "type": "object",
        "properties": get_model_properties(model),
        "required": get_model_required_fields(model)
    }  # todo abstract classes


def get_model_properties(model: Type[AvishanModel]) -> dict:
    data = {}
    for field in model.get_fields():
        data = {**data, **get_field_object(field)}

    return data


def get_field_object(field: models.Field) -> dict:
    data = {
        field.name: None
    }
    if isinstance(field, models.BooleanField):
        data[field.name] = {
            'type': "boolean"
        }
    elif isinstance(field, (models.IntegerField, models.AutoField)):
        data[field.name] = {
            'type': "number"
        }
    elif isinstance(field, models.FloatField):
        data[field.name] = {
            'type': "float"
        }
    elif isinstance(field, (models.CharField, models.TextField)):
        data[field.name] = {
            'type': "string"
        }
    elif isinstance(field, models.DateTimeField):
        data[field.name] = {
            'type': "date-time"
        }
    elif isinstance(field, models.DateField):
        data[field.name] = {
            'type': "date"
        }
    elif isinstance(field, models.TimeField):
        data[field.name] = {
            'type': "string"
        }
    elif isinstance(field, (models.OneToOneField, models.ForeignKey)):
        data[field.name] = {
            '$ref': f"#/components/schemas/{field.related_model.class_name()}"
        }
    elif isinstance(field, models.FileField):
        data[field.name] = {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'integer'
                },
                'url': {
                    'type': 'string'
                }
            }
        }
    else:
        raise NotImplementedError()
    if len(field.choices) > 0:
        data[field.name]['enum'] = [item[1] for item in field.choices]
    return data


def get_field_added_data(field: models.Field) -> dict:
    data = {}
    if field.null:
        data['nullable']: True
    return data


def get_model_required_fields(model: Type[AvishanModel]) -> list:
    data = []
    for field in model.get_full_fields():
        if AvishanModel.is_field_required(field):
            data.append(field.name)

    return data
