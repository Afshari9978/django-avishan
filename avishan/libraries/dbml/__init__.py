from typing import Type, List

import stringcase
from django.db import models
from django.db.models import NOT_PROVIDED

from avishan.models import AvishanModel


def create_dbml_file(address: str):
    dbml = {
        'tables': []
    }
    for model in AvishanModel.get_models():
        dbml['tables'].append(convert_model_to_object(model))
    print(f"DBML READ FOR {len(dbml['tables'])} TABLES")
    from pathlib import Path
    folder = ""
    parts = address.split("/")
    for part in parts[:-1]:
        folder += part + "/"
    Path(folder).mkdir(parents=True, exist_ok=True)
    writer(dbml, address)
    print("DBML FILE CREATED")


def convert_model_to_object(model: Type[AvishanModel]) -> dict:
    data = {
        "name": model.class_name(),
        "columns": [],
        "many_to_many": []
    }
    for field in model.get_full_fields():
        if isinstance(field, models.ManyToManyField):
            data['many_to_many'].append(handle_many_to_many_field(field))
        # todo add note to field
        else:
            data["columns"].append(handle_field(field))
    return data


def handle_field(field: models.Field) -> dict:
    data = {
        'column_name': field.name,
        'column_type': None,
        'column_settings': handle_field_settings(field)
    }
    if isinstance(field, models.OneToOneField):
        data['column_type'] = 'integer'
        data['column_name'] = data['column_name'] + "_id"
        data['column_settings'] = [f"ref: - {field.related_model.class_name()}.id"] + data['column_settings']
    if isinstance(field, models.ForeignKey):
        data['column_type'] = 'integer'
        data['column_name'] = data['column_name'] + "_id"
        data['column_settings'] = [f"ref: > {field.related_model.class_name()}.id"] + data['column_settings']
    elif isinstance(field, (models.BigIntegerField, models.BigAutoField)):
        data['column_type'] = 'long'
    elif isinstance(field, (models.AutoField, models.IntegerField)):
        data['column_type'] = 'integer'
    elif isinstance(field, models.CharField):
        data['column_type'] = f'varchar({field.max_length})'
    elif isinstance(field, models.BooleanField):
        data['column_type'] = 'boolean'
    elif isinstance(field, models.TextField):
        data['column_type'] = 'text'
    elif isinstance(field, models.FloatField):
        data['column_type'] = 'float'
    elif isinstance(field, models.DateTimeField):
        data['column_type'] = 'datetime'
    elif isinstance(field, models.FileField):
        data['column_name'] = 'url'
        data['column_type'] = 'string'
    else:
        raise NotImplementedError()
    if len(data['column_settings']) == 0:
        del data['column_settings']
    return data


def handle_many_to_many_field(field: models.ManyToManyField) -> dict:
    data = {
        "name": ("m2m" + (field.model.class_name()) + stringcase.titlecase(field.name))[:-1],
        "columns": [
            {
                'column_name': stringcase.snakecase(field.model.class_name()) + "_id",
                'column_type': 'integer',
                'column_settings': [f"ref: > {field.model.class_name()}.id"]
            }, {
                'column_name': stringcase.snakecase(field.related_model.class_name()) + "_id",
                'column_type': 'integer',
                'column_settings': [f"ref: > {field.related_model.class_name()}.id"]
            }
        ],
        "many_to_many": []
    }
    data['name'] = data['name'].replace(" ", "")
    return data


def handle_field_settings(field: models.Field) -> list:
    data = []
    if isinstance(field, models.DateTimeField) and (field.auto_now or field.auto_now_add):
        data.append('note: "auto created"')
    if field.primary_key:
        data.append("primary key")
    if field.null:
        data.append("null")
    if field.unique:
        data.append("unique")
    if field.default is not NOT_PROVIDED:
        data.append(f"default: {handle_value(field.default)}")
    return data


def handle_value(value) -> str:
    if value is False:
        return "false"
    if value is True:
        return "true"
    if value is None:
        return "null"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        return f'"{value}"'
    raise NotImplementedError()


def writer(dbml: dict, file_address: str):
    lines = []
    for table in dbml['tables']:
        lines += write_table(table)

    f = open(file_address, 'w')
    for line in lines:
        f.write(line + "\n")
    f.close()


def write_table(data: dict) -> List[str]:
    lines = [
        "Table %s {" % data['name']
    ]
    for column in data['columns']:
        lines.append(write_column(column))
    lines.append("}")
    for many in data['many_to_many']:
        lines += write_table(many)
    return lines


def write_column(data) -> str:
    text = f"    {data['column_name']} {data['column_type']}"

    if 'column_settings' in data.keys():
        text += " ["
        for string in data['column_settings']:
            text += string + ", "
        text = text[:-2]
        text += "]"

    return text
