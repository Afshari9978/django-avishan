from typing import TextIO, Type

from django.db.models import Field

from ..models import AvishanModel
from .model_functions import find_models, get_app_names


def create_raml_documentation(project_name: str):
    raml = {}
    write_header(raml, project_name)
    write_security(raml)
    write_types(raml)
    write_base_resources(raml)

    write_raml_to_file(raml, project_name)


def open_app_documentation_file(project_name: str) -> TextIO:
    return open('%s_documentation.raml' % project_name, 'w')


def write_raml_to_file(raml: dict, project_name: str):
    file = open_app_documentation_file(project_name)
    file.writelines([
        '#%RAML 1.0\n',
        'title: %s\n' % raml['title'],
        'version: %s\n' % raml['version'],
        'baseUri: %s\n' % raml['baseUri'],
    ])
    write_dict_to_file(raml['types'], file, 'types', 0)
    # todo save dict to file
    file.close()


def write_header(raml: dict, project_name: str):
    from avishan_config import BASE_URLS
    raml['title'] = project_name
    raml['version'] = 'v1'
    raml['baseUri'] = BASE_URLS[0]


def write_types(raml: dict):
    raml['types'] = {}
    for model in find_models('avishan'):
        raml['types'][model.__name__] = describe_model(model)
    for app_name in get_app_names():
        for model in find_models(app_name):
            raml['types'][model.__name__] = describe_model(model)
    if raml['types'] == {}:
        del raml['types']


def describe_model(model: Type[AvishanModel]) -> dict:
    model_dict = {
        'type': 'object',
        'properties': {}
    }

    for field in model.get_fields():
        model_dict['properties'][field.name] = describe_field(field)

    temp = describe_model_examples(model)
    if temp != {}:
        model_dict['examples'] = temp
    return model_dict


def describe_field(field: Field) -> dict:
    field_dict = {}

    from django.db.models import DateTimeField, DateField, TimeField, CharField, TextField, FileField, \
        BooleanField, IntegerField, FloatField, ManyToManyField, ForeignKey, AutoField
    if isinstance(field, (CharField, TextField)):
        field_dict['type'] = "string"
    elif isinstance(field, (IntegerField, FloatField, AutoField)):
        field_dict['type'] = 'number'
    elif isinstance(field, TimeField):
        field_dict['type'] = 'time-only'
    elif isinstance(field, DateTimeField):
        field_dict['type'] = 'datetime'
    elif isinstance(field, DateField):
        field_dict['type'] = 'date-only'
    elif isinstance(field, BooleanField):
        field_dict['type'] = 'boolean'
    elif isinstance(field, FileField):
        field_dict['type'] = 'file'
    elif isinstance(field, ManyToManyField):
        field_dict['type'] = field.related_model.class_name()
    elif isinstance(field, ForeignKey):
        field_dict['type'] = field.related_model.class_name()

    field_dict['required'] = AvishanModel.is_field_required(field)
    return field_dict


def describe_model_examples(model: Type[AvishanModel]) -> dict:
    # todo
    return {}


def write_model_additional_data(raml: dict, model: Type[AvishanModel]):
    # todo
    pass


def get_indent(stage: int) -> str:
    return '  ' * stage


def write_dict_to_file(data: dict, file: TextIO, name: str, indent_stage: int):
    file.write(get_indent(indent_stage) + name + ":\n")
    for key, value in data.items():
        if isinstance(value, dict):
            write_dict_to_file(value, file, key, indent_stage + 1)
        else:
            if value is True:
                value = 'true'
            elif value is False:
                value = 'false'
            file.write(get_indent(indent_stage + 1) + "%s: %s\n" % (key, value))


def write_base_resources(raml: dict):
    raml['/api'] = {
        '/v1': {
            'description': 'the first version of api',
            '/test': {
                'description': 'its just a test'
            },
            '/auth': {
                'description': 'authentication part of project',
                '/check_phone/{role}/{phone}': {
                    'get': {
                        'uriParameters': {
                            'role': {
                                'type': 'string',
                                'description': 'can be chosen from: user, admin'
                            },
                            'phone': {
                                'type': 'string',
                                'description': 'user entered phone'
                            },
                        },
                        'responses': {
                            '200': {
                                'body': {
                                    'user': 'User',
                                    'token': 'string'
                                },
                                'description': 'old user'
                            },
                            '201': {
                                'body': {
                                    'user': 'User',
                                    'token': 'string'
                                },
                                'description': 'new user'
                            },
                            '408': {
                                'description': 'پیامک قبلی همین چند دقیقه پیش اومده'
                            },
                            '400': {
                                'description': 'global errors',
                                'examples': {
                                    '1': 'حساب کاربری پیدا نشد'
                                }
                            }
                        }
                    },
                    '/check_code/{role}/{phone}/{code}': {
                        'get': {
                            'uriParameters': {
                                'role': {
                                    'type': 'string',
                                    'description': 'can be chosen from: user, admin'
                                },
                                'phone': {
                                    'type': 'string',
                                    'description': 'user entered phone'
                                },
                                'code': {
                                    'type': 'string',
                                    'description': 'user entered code'
                                }
                            },
                            'responses': {
                                '200': {
                                    'body': {
                                        'user': 'User',
                                        'token': 'string'
                                    },
                                    'description': 'old user'
                                },
                                '201': {
                                    'body': {
                                        'user': 'User',
                                        'token': 'string'
                                    },
                                    'description': 'new user'
                                },
                                '400': {
                                    'description': 'global errors',
                                    'examples': {
                                        '1': 'کد ورود برای این شماره پیدا نشد، لطفا مجددا کد دریافت کنید',
                                        '2': 'زمان اعتبار این کد به اتمام رسیده، لطفا مجددا کد دریافت کنید',
                                        '3': 'کد وارد شده اشتباه است',
                                        '4': 'حساب کاربری پیدا نشد'
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    raml['/api'] = {

    }


def write_security(raml: dict):
    raml['securitySchemes'] = {
        'token-authentication': {
            'type': 'Pass Through',
            'describedBy': {
                'headers': {
                    'token': {
                        'type': 'string'
                    }
                }
            }
        }
    }
