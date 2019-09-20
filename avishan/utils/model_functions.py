import importlib
import pkgutil
from datetime import datetime, date, time
from typing import Union, List, Optional, Type

from django.db.models import QuerySet, Model
from django.db.models.fields.files import ImageFieldFile, FieldFile

from ..models import AvishanModel, Image
from ..utils.bch_datetime import BchDatetime


# def objectify_model(model: Union[Model, QuerySet, list], compact: bool = False, except_list: list = None,
#                     visible_list: list = None) -> Union[dict, List[dict]]:
#     if isinstance(model, QuerySet):
#         objectified = []
#         for item in model:
#             objectified.append(
#                 objectify_model(item, compact=compact, except_list=except_list, visible_list=visible_list))
#         return objectified
#
#     objectified = {}
#
#     if model is None:
#         return objectified
#
#     if not visible_list:
#         visible_list = []
#     if not except_list:
#         except_list = []
#     field_names = []
#     for field in model._meta.fields:
#         field_names.append(field.name)
#
#     field_names = filter_added_properties(field_names, model)
#     field_names = filter_private_fields(field_names, model, visible_list)
#     if compact:
#         field_names = filter_compact_fields(field_names, model)
#     field_names = filter_except_list(field_names, except_list)
#
#     for field_name in field_names:
#         data = model.__getattribute__(field_name)
#
#         # if not data and ('date' in field_name or 'time' in field_name):
#         #     objectified[field_name] = {}
#
#         if isinstance(data, datetime) or isinstance(data, date):
#             objectified[field_name] = BchDatetime(data).to_dict(full=True)
#         elif isinstance(data, Model):
#             objectified[field_name] = objectify_model(data)
#         elif isinstance(data, ImageFieldFile) or isinstance(data, FieldFile):
#             objectified['url'] = data.url
#         elif isinstance(data, time):
#             objectified[field_name] = {
#                 'hour': data.hour, 'minute': data.minute, 'second': data.second, 'microsecond': data.microsecond
#             }
#         else:
#             objectified[field_name] = data
#
#     return objectified


def filter_added_properties(field_names, model: Model):
    new_field_names = field_names[:]
    try:
        added_properties = model.added_properties
    except AttributeError:
        added_properties = []

    for added_property in added_properties:
        if added_property not in new_field_names:
            new_field_names.append(added_property)

    return new_field_names


def filter_private_fields(field_names: list, model: Model, visible_list: list):
    try:
        private_fields = model.private_fields
    except AttributeError:
        private_fields = []

    if len(visible_list) > 0:
        for field_name in field_names[:]:
            if field_name not in visible_list:
                field_names.remove(field_name)
    else:
        for field_name in field_names[:]:
            if field_name in private_fields:
                field_names.remove(field_name)

    return field_names


def filter_compact_fields(field_names, model: Model):
    try:
        compact_fields = model.compact_fields
    except AttributeError:
        compact_fields = field_names

    for field_name in field_names[:]:
        if field_name not in compact_fields:
            field_names.remove(field_name)

    return field_names


def filter_except_list(field_names, except_list):
    for field_name in field_names[:]:
        if field_name in except_list:
            field_names.remove(field_name)

    return field_names


def find_models(app_name: str = None) -> List[Type[AvishanModel]]:
    if not app_name:
        total = AvishanModel.__subclasses__()
        for item in total[:]:
            if len(item.__subclasses__()) > 0:
                total += item.__subclasses__() # todo should be recursive
        return list(set(total))
    return [x for x in find_models() if x._meta.app_label == app_name]


def find_non_abstract_models(app_name: str = None) -> List[Type[AvishanModel]]:
    return [x for x in find_models(app_name) if x._meta.abstract is False]


def find_model_by_plural_name(name: str) -> Optional[Type[AvishanModel]]:
    for model in find_models():
        if model.class_plural_snake_case_name() == name:
            return model
    return None


def get_sum_on_field(query_set: QuerySet, field_name: str) -> int:
    from django.db.models import Sum
    total = query_set.aggregate(Sum(field_name))[field_name + "__sum"]
    if total:
        return total
    return 0



def get_app_names() -> List[str]:
    from django.apps import apps
    return [key.name for key in apps.get_app_configs() if
            (not key.name.startswith('django.') and key.name != 'avishan')]


def save_image_from_url(url: str) -> Image:
    import requests

    from django.core.files import File
    from django.core.files.base import ContentFile
    from django.core.files.temp import NamedTemporaryFile

    # r = requests.get(url)
    name = url.split('/')[-1]
    if '.' not in name:
        name = url.split('/')[-2]

    image_temp = open(url, 'rb')
    # img_temp = NamedTemporaryFile(delete=True)
    # img_temp.write(r.content)
    # img_temp.flush()

    image = Image.objects.create()
    image.file.save(name, File(image_temp), save=True)

    image.save()
    return image
