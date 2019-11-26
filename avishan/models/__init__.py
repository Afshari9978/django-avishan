import datetime
from typing import List, Type, Tuple, Optional, Union

from django.db import models

from django.db.models import NOT_PROVIDED

from avishan import current_request
from avishan.exceptions import ErrorMessageException
from avishan.misc import translatable
from avishan.misc.bch_datetime import BchDatetime


class AvishanModel(models.Model):
    # todo 0.2.1: use manager or simply create functions here?
    class Meta:
        abstract = True

    """
    Django admin default values. Set this for all inherited models
    """
    date_hierarchy = None
    list_display = None
    list_filter = []
    list_max_show_all = 300
    list_per_page = 100
    raw_id_fields = []
    readonly_fields = []
    search_fields = []

    """
    CRUD functions
    """

    @classmethod
    def get(cls, avishan_to_dict: bool = False, avishan_raise_400: bool = False,
            **kwargs) -> Union['AvishanModel', dict]:
        # todo 0.2.1 compact, private, added properties
        if avishan_to_dict:
            return cls.get(avishan_to_dict=False, avishan_raise_400=avishan_raise_400, **kwargs).to_dict()

        try:
            return cls.objects.get(**kwargs)
        except cls.DoesNotExist as e:
            if avishan_raise_400:
                raise ErrorMessageException(translatable(
                    EN="Chosen " + cls.__name__ + " doesnt exist",
                    FA=f"{cls.__name__} انتخاب شده موجود نیست"
                ))
            raise e

    @classmethod
    def filter(cls, avishan_to_dict: bool = False, **kwargs):
        if avishan_to_dict:
            return [item.to_dict() for item in cls.filter(**kwargs)]

        if len(kwargs.items()) > 0:
            return cls.objects.filter(**kwargs)
        else:
            return cls.objects.all()

    @classmethod
    def all(cls, avishan_to_dict: bool = False):
        return cls.filter(avishan_to_dict)

    @classmethod
    def create(cls, **kwargs) -> 'AvishanModel':
        create_kwargs, after_create_kwargs = cls._clean_model_data_kwargs(**kwargs)
        created = cls.objects.create(**create_kwargs)

        if after_create_kwargs:
            for key, value in after_create_kwargs.items():
                for item in value:
                    created.__getattribute__(key).add(item)
            created.save()
        return created

    def update(self, **kwargs):
        base_kwargs, many_to_many_kwargs = self.__class__._clean_model_data_kwargs(**kwargs)
        # todo 0.2.3: check for change. if not changed, dont update
        for key, value in base_kwargs.items():
            # todo 0.2.3 check value types
            self.__setattr__(key, value)

        if many_to_many_kwargs:
            for key, value in many_to_many_kwargs.items():
                # todo 0.2.1 many to many efficient add/remove
                self.__getattribute__(key).clear()
                for item in value:
                    self.__getattribute__(key).add(item)
        self.save()
        return self

    def remove(self):
        temp = self.to_dict()
        self.delete()
        return temp

    @classmethod
    def create_or_update(cls, fixed_kwargs: dict, new_additional_kwargs: dict) -> Tuple[Type['AvishanModel'], bool]:
        """
        Create object if doesnt exists. Else update it
        :param fixed_kwargs: key values to find object in db
        :param new_additional_kwargs: new changing kwargs
        :return: found/created object and True if created, False if found
        """
        try:
            found = cls.objects.get(**fixed_kwargs)
            for key, value in new_additional_kwargs.items():
                found.__setattr__(key, value)
            found.save()
            return found, False
        except cls.DoesNotExist:
            return cls.objects.create(
                **{**fixed_kwargs, **new_additional_kwargs}
            ), True

    """
    Model util functions
    """

    def to_dict(self) -> dict:
        """
        Convert object to dict
        :return:
        """

        # todo 0.2.1: compact
        dicted = {}

        field_names = []
        for field in self.get_full_fields():
            field_names.append(field.name)

        for field in self.get_full_fields():
            if field.name not in field_names:
                continue

            value = self.__getattribute__(field.name)
            if value is None:
                dicted[field.name] = {}
            elif isinstance(field, models.DateField):
                dicted[field.name] = BchDatetime(value).to_dict(full=True)
            elif isinstance(field, (models.OneToOneField, models.ForeignKey)):
                dicted[field.name] = value.to_dict()
            elif isinstance(field, models.ManyToManyField):
                dicted[field.name] = []
                for item in value.all():
                    dicted[field.name].append(item.to_dict())
            elif isinstance(value, datetime.time):
                dicted[field.name] = {
                    'hour': value.hour, 'minute': value.minute, 'second': value.second, 'microsecond': value.microsecond
                }
            else:
                dicted[field.name] = value

        return dicted

    @classmethod
    def _clean_model_data_kwargs(cls, on_update: bool = False, **kwargs):
        base_kwargs = {}
        many_to_many_kwargs = {}

        if not current_request['is_api']:
            kwargs = cls._clean_form_post(kwargs)

        for field in cls.get_full_fields():
            """Check exists"""
            if cls.is_field_readonly(field):
                continue

            if cls.is_field_required(field) and not on_update and field.name not in kwargs.keys():
                raise ErrorMessageException(translatable(
                    EN=f'Field {field.name} not found in object {cls.class_name()}, and it\'s required.',
                ))

            elif field.name not in kwargs.keys():
                continue

            """Read data part"""
            if isinstance(field, (models.OneToOneField, models.ForeignKey)):
                if isinstance(kwargs[field.name], models.Model):
                    base_kwargs[field.name] = kwargs[field.name]
                else:
                    base_kwargs[field.name] = field.related_model.__get_object_from_dict(kwargs[field.name])
            elif isinstance(field, models.ManyToManyField):
                many_to_many_kwargs[field.name] = []
                for input_item in kwargs[field.name]:
                    if isinstance(input_item, models.Model):
                        item_object = input_item
                    else:
                        item_object = field.related_model.__get_object_from_dict(input_item)
                    many_to_many_kwargs[field.name].append(item_object)
            else:
                base_kwargs[field.name] = cls.cast_field_data(kwargs[field.name], field)
        return base_kwargs, many_to_many_kwargs

    @classmethod
    def _clean_form_post(cls, kwargs: dict) -> dict:
        output = {}
        for key, value in kwargs.items():
            if key.endswith("_id"):
                output[key[:-3]] = {'id': int(value)}
            elif key.endswith('_ids'):
                # todo 0.2.0: check it
                output[key[:-4]] = []
                for related_id in value:
                    output[key[:-4]].append({'id': int(related_id)})
            elif key.endswith('_d'):
                date_parts = value.split('-')
                output[key[:-2]] = BchDatetime(date_parts[2], date_parts[1], date_parts[0]).to_date()
            else:
                output[key] = value

        return output

    @classmethod
    def class_name(cls) -> str:
        return cls.__name__

    @classmethod
    def class_snake_case_name(cls) -> str:
        import re
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', cls.class_name())
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    @classmethod
    def class_plural_snake_case_name(cls) -> str:
        return cls.class_snake_case_name() + "s"

    @classmethod
    def app_name(cls) -> str:
        return cls._meta.app_label

    @staticmethod
    def get_non_abstract_models(app_name: str = None) -> List[Type['AvishanModel']]:
        return [x for x in AvishanModel.get_models(app_name) if x._meta.abstract is False]

    @staticmethod
    def get_models(app_name: str = None) -> List[Type['AvishanModel']]:
        # todo 0.2.1 check for app name to be in avishan_config file
        def get_sub_classes(parent):
            subs = [parent]
            for child in parent.__subclasses__():
                subs += get_sub_classes(child)
            return subs

        total = []
        if not app_name:
            for model in AvishanModel.__subclasses__():
                total += get_sub_classes(model)
            return list(set(total))

        return [x for x in AvishanModel.get_models() if x._meta.app_label == app_name]

    @staticmethod
    def get_model_with_class_name(class_name: str) -> Optional[Type['AvishanModel']]:
        for item in AvishanModel.get_models():
            if item.class_name() == class_name:
                return item
        return None

    @staticmethod
    def get_model_by_plural_name(name: str) -> Optional[Type['AvishanModel']]:
        for model in AvishanModel.get_non_abstract_models():
            if model.class_plural_snake_case_name() == name:
                return model
        return None

    @staticmethod
    def run_apps_check():
        # todo 0.2.0 create config file and its classes. add needed fields
        from importlib import import_module
        from avishan.utils import create_avishan_config_file

        try:
            import avishan_config
        except ImportError:
            create_avishan_config_file()

        for app_name in AvishanModel.get_app_names():

            try:
                import_module(app_name)
            except ModuleNotFoundError:
                # todo 0.2.2 raise some error somewhere
                continue
            try:
                init_file = import_module(app_name + ".avishan_config")
            except ModuleNotFoundError:
                create_avishan_config_file(app_name)
                continue
            try:
                init_file.check()
            except AttributeError as e:
                # todo 0.2.2 raise some error somewhere
                continue

    @staticmethod
    def get_app_names() -> List[str]:
        from django.apps import apps
        from avishan_config import AvishanConfig
        return [key.name for key in apps.get_app_configs() if
                key.name in AvishanConfig.MONITORED_APPS_NAMES]

    @classmethod
    def get_fields(cls) -> List[models.Field]:
        return list(cls._meta.fields)

    @classmethod
    def get_full_fields(cls) -> List[models.Field]:
        return list(cls._meta.fields + cls._meta.many_to_many)

    @classmethod
    def get_field(cls, field_name: str) -> models.Field:
        for item in cls.get_fields():
            if item.name == field_name:
                return item
        raise ValueError(translatable(
            EN=f'field {field_name} not found in model {cls.class_name()}'
        ))

    @classmethod
    def is_field_identifier_for_model(cls, field: models.Field) -> bool:
        """
        Checks if field is enough for finding an object from db.
        :param field: for example for 'id' or other unique fields, it will be True
        :return:
        """
        return field.primary_key or field.unique

    @staticmethod
    def is_field_readonly(field: models.Field) -> bool:
        """
        Checks if field is read-only type and must not entered by user
        :param field: for example auto create date-times
        :return:
        """
        if (isinstance(field, models.DateField) or isinstance(field, models.DateTimeField) or
            isinstance(field, models.TimeField)) and (field.auto_now or field.auto_now_add):
            return True
        if field.primary_key:
            return True
        return False

    @staticmethod
    def is_field_required(field: models.Field) -> bool:
        """
        Checks if field is required and create-blocking for model
        :param field:
        :return: True if required
        """
        if field.name == 'id' or field.default != NOT_PROVIDED or \
                (isinstance(field, models.DateField) or isinstance(field, models.TimeField) and (
                        field.auto_now or field.auto_now_add)):
            return False
        if isinstance(field, models.ManyToManyField):
            return False

        if field.blank or field.null:
            return False

        return True

    @classmethod
    def cast_field_data(cls, data, field):
        if isinstance(field, (models.CharField, models.TextField)):
            cast = str
        elif isinstance(field, (models.IntegerField, models.AutoField)):
            cast = int
        elif isinstance(field, models.FloatField):
            cast = float
        elif isinstance(field, models.TimeField):
            if not isinstance(data, datetime.time):
                cast = datetime.time
            else:
                cast = None
        elif isinstance(field, models.DateTimeField):
            if not isinstance(data, datetime.datetime):
                cast = datetime.datetime
            else:
                cast = None
        elif isinstance(field, models.DateField):
            if not isinstance(data, datetime.date):
                cast = datetime.date
            else:
                cast = None
        elif isinstance(field, models.BooleanField):
            cast = bool
        elif isinstance(field, models.ManyToManyField):
            cast = field.related_model
        elif isinstance(field, models.ForeignKey):
            cast = field.related_model
        else:
            raise NotImplementedError(translatable(
                EN='cast_field_data not defined cast type',
            ))

        if cast is None:
            return data
        if isinstance(cast, AvishanModel):
            if not isinstance(data, dict):
                raise ValueError('ForeignKey or ManyToMany relation should contain dict with id')
            output = cast.objects.get(id=int(data['id']))
        elif isinstance(cast, datetime.datetime):
            if not isinstance(data, dict):
                raise ValueError('Datetime should contain dict')
            output = BchDatetime(data).to_datetime()
        elif isinstance(cast, datetime.date):
            if not isinstance(data, dict):
                raise ValueError('Date should contain dict')
            output = BchDatetime(data).to_date()
        else:
            output = cast(data)

        return output

    @classmethod
    def __get_object_from_dict(cls, input_dict: dict) -> 'AvishanModel':
        return cls.get(**input_dict)

    def get_data_from_field(self, field_name: str):
        from avishan_config import AvishanConfig
        field = self.get_field(field_name)
        if len(field.choices) > 0:
            for choice in field.choices:
                if choice[0] == self.__getattribute__(field_name):
                    return choice[1]
        if isinstance(field, models.DateTimeField):
            if AvishanConfig.IS_JALALI_DATETIME:
                return BchDatetime(self.__getattribute__(field_name)).to_str('%Y/%m/%d %H:%M:%S')
            return self.__getattribute__(field_name).strftime("%Y/%m/%d %H:%M:%S")
        if isinstance(field, models.DateField):
            if AvishanConfig.IS_JALALI_DATETIME:
                return BchDatetime(self.__getattribute__(field_name)).to_str('%Y/%m/%d')
            return self.__getattribute__(field_name).strftime("%Y/%m/%d")
        if isinstance(field, models.TimeField):
            return self.__getattribute__(field_name).strftime("%H:%M:%S")
        return self.__getattribute__(field_name)
