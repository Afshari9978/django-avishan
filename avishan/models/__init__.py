import datetime
from typing import List, Type, Tuple, Optional, Union

from django.db import models

from django.db.models import NOT_PROVIDED

from avishan.exceptions import ErrorMessageException
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
                raise ErrorMessageException("Chosen " + cls.__name__ + " doesnt exist")
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
        create_kwargs, after_create_kwargs = cls._clean_create_kwargs(**kwargs)
        created = cls.objects.create(**create_kwargs)

        if after_create_kwargs:
            for key, value in after_create_kwargs.items():
                for item in value:
                    created.__getattribute__(key).add(item)
        created.save()
        return created

    def update(self, **kwargs):
        in_time_kwargs, many_to_many_kwargs = self.__class__._clean_create_kwargs(**kwargs)
        # todo 0.2.1: remove identifier attributes to prevent update on them
        # todo 0.2.3: check for change. if not changed, dont update
        for key, value in in_time_kwargs.items():
            # todo 0.2.3 check value types
            self.__setattr__(key, value)

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
    def _clean_create_kwargs(cls, **kwargs):
        create_kwargs = {}
        after_create_kwargs = {}
        for field in cls.get_full_fields():
            if cls.is_field_identifier_for_model(field) or (
                    isinstance(field, (models.DateField, models.TimeField)) and (field.auto_now or field.auto_now_add)):
                continue
            elif cls.is_field_required(field) and field.name not in kwargs.keys():
                raise ErrorMessageException(
                    f'Field {field.name} not found in object {cls.class_name()}, and it\'s required.'
                )
            elif field.name not in kwargs.keys():
                continue
            elif isinstance(field, (models.OneToOneField, models.ForeignKey)):
                if isinstance(kwargs[field.name], models.Model):
                    create_kwargs[field.name] = kwargs[field.name]
                else:
                    create_kwargs[field.name] = field.related_model.__get_object_from_dict(kwargs[field.name])
            elif isinstance(field, models.ManyToManyField):
                after_create_kwargs[field.name] = []
                for input_item in kwargs[field.name]:
                    if isinstance(input_item, models.Model):
                        item_object = input_item
                    else:
                        item_object = field.related_model.__get_object_from_dict(input_item)
                    after_create_kwargs[field.name].append(item_object)
            else:
                create_kwargs[field.name] = kwargs[field.name]
                if isinstance(kwargs[field.name], BchDatetime):
                    if isinstance(field, models.DateTimeField):
                        create_kwargs[field.name] = kwargs[field.name].to_datetime()
                    elif isinstance(field, models.DateField):
                        create_kwargs[field.name] = kwargs[field.name].to_date()
                    elif isinstance(field, models.TimeField):
                        create_kwargs[field.name] = kwargs[field.name].to_time()
                    else:
                        raise ErrorMessageException('Error in datetime system')
        return create_kwargs, after_create_kwargs

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
    def find_non_abstract_models(app_name: str = None) -> List[Type['AvishanModel']]:
        return [x for x in AvishanModel.find_models(app_name) if x._meta.abstract is False]

    @staticmethod
    def find_models(app_name: str = None) -> List[Type['AvishanModel']]:

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

        return [x for x in AvishanModel.find_models() if x._meta.app_label == app_name]

    @staticmethod
    def find_model_with_class_name(class_name: str) -> Optional[Type['AvishanModel']]:
        for item in AvishanModel.find_models():
            if item.class_name() == class_name:
                return item
        return None

    @staticmethod
    def find_model_by_plural_name(name: str) -> Optional[Type['AvishanModel']]:
        for model in AvishanModel.find_non_abstract_models():
            if model.class_plural_snake_case_name() == name:
                return model
        return None

    @classmethod
    def get_fields(cls) -> List[models.Field]:
        return cls._meta.fields

    @classmethod
    def get_full_fields(cls) -> List[models.Field]:
        return cls.get_fields() + cls._meta.many_to_many

    @classmethod
    def get_field(cls, field_name: str) -> models.Field:
        for item in cls.get_fields():
            if item.name == field_name:
                return item
        raise ValueError(f'field {field_name} not found in model {cls.class_name()}')



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
    def __get_object_from_dict(cls, input_dict: dict) -> 'AvishanModel':
        return cls.get(**input_dict)
