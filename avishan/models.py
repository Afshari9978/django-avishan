import random
import re
import string
from inspect import Parameter
from typing import List, Type, Union, Tuple, Dict

import pytz
import stringcase
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.utils import timezone

from avishan import current_request
from avishan.configure import get_avishan_config, AvishanConfigFather
from avishan.exceptions import AuthException, ErrorMessageException
from avishan.libraries.faker import AvishanFaker
from avishan.misc import status
from avishan.misc.translation import AvishanTranslatable
from avishan.descriptor import DirectCallable

import datetime
from typing import Optional

from django.db import models

# todo related name on abstracts
# todo app name needed for models
from avishan.models_extensions import AvishanModelDjangoAdminExtension, AvishanModelModelDetailsExtension, \
    AvishanModelFilterExtension


class AvishanModel(
    models.Model,
    AvishanFaker,
    AvishanModelDjangoAdminExtension,
    AvishanModelModelDetailsExtension,
    AvishanModelFilterExtension
):
    # todo 0.2.1: use manager or simply create functions here?
    # todo 0.2.0 relation on_delete will call our remove() ?
    class Meta:
        abstract = True

    """
    Models default settings
    """
    to_dict_private_fields: List[Union[models.Field, str]] = []
    export_ignore: bool = False  # todo check
    to_dict_added_fields: List[Tuple[str, Type[type]]] = []

    @classmethod
    def direct_callable_methods(cls) -> List[DirectCallable]:
        """
        method name, response json key, (request json key)
        :return:
        :rtype: DirectCallable
        """
        return [
            DirectCallable(
                model=cls,
                target_name='all',
                url=''
            ),
            DirectCallable(
                model=cls,
                target_name='create',
                response_json_key=cls.class_snake_case_name(),
                method=DirectCallable.METHOD.POST,
                url='',
                on_empty_args=cls._create_default_args()
            ),
            DirectCallable(
                model=cls,
                target_name='get',
                response_json_key=cls.class_snake_case_name(),
                url='/{id}',
                is_class_method=False
            ),
            DirectCallable(
                model=cls,
                target_name='update',
                response_json_key=cls.class_snake_case_name(),
                request_json_key=cls.class_snake_case_name(),
                url='/{id}',
                method=DirectCallable.METHOD.PUT,
                on_empty_args=cls._update_default_args()
            ),
            DirectCallable(
                model=cls,
                target_name='remove',
                response_json_key=cls.class_snake_case_name(),
                url='/{id}',
                method=DirectCallable.METHOD.DELETE
            )
        ]

    @classmethod
    def openapi_documented_methods(cls):
        return cls.direct_callable_methods()

    @classmethod
    def openapi_documented_fields(cls) -> List[str]:
        """Returns list of field names should be visible by openapi documentation

        :return: list of document visible fields
        :rtype: List[str]
        """
        total = list(cls._meta.fields + cls._meta.many_to_many)
        privates = []
        for item in cls.to_dict_private_fields:
            if not isinstance(item, str):
                privates.append(item.name)
            else:
                privates.append(item)

        return [field.name for field in total if field.name not in privates]

    @classmethod
    def get(cls, avishan_raise_400: bool = False,
            **kwargs):
        from avishan.exceptions import ErrorMessageException

        try:
            return cls.objects.get(**kwargs)
        except cls.DoesNotExist as e:
            if avishan_raise_400:
                raise ErrorMessageException(AvishanTranslatable(
                    EN="Chosen " + cls.__name__ + " doesnt exist",
                    FA=f"{cls.__name__} انتخاب شده موجود نیست"
                ))
            raise e

    @classmethod
    def _get_documentation_params(cls):
        return stringcase.titlecase(cls.class_name()), cls.class_name(), cls.class_name()

    @classmethod
    def _get_documentation_raw(cls):
        return """Get %s item

        :response %s 200: Success
        :return %s: Item
        """

    @classmethod
    def filter(cls, **kwargs):
        # todo show filterable fields on doc
        # todo use django-filter for on-url filter

        if 'request' in current_request.keys():
            for item in current_request['request'].GET.keys():
                if item.startswith('filter_'):
                    field = cls.get_field(item[7:])
                    kwargs[field.name] = field.related_model.get(id=current_request['request'].GET[item])

        if len(kwargs.items()) > 0:
            return cls.objects.filter(**kwargs)
        else:
            return cls.objects.all()

    @classmethod
    def all(cls):
        return cls.filter()

    @classmethod
    def _all_documentation_params(cls):
        return stringcase.titlecase(cls.class_plural_name()), cls.class_name(), cls.class_name()

    @classmethod
    def _all_documentation_raw(cls):
        return """Get %s
        
        :response List[%s] 200: Success
        :return List[%s]: Items, usually ordered by id, acceding
        """

    @classmethod
    def create(cls, **kwargs):

        create_kwargs, many_to_many_objects, after_creation = cls._clean_model_data_kwargs(**kwargs)
        created = cls.objects.create(**create_kwargs)

        if many_to_many_objects:
            for key, value in many_to_many_objects.items():
                for item in value:
                    created.__getattribute__(key).add(item)
            created.save()
        for after_create in after_creation:
            for target_object in after_create['target_objects']:
                after_create['target_model'].create(**{
                    after_create['created_for_field'].name: created,
                    **target_object
                })
        return created

    @classmethod
    def _create_documentation_params(cls):
        return stringcase.titlecase(cls.class_name()), cls.class_name(), cls.class_name()

    @classmethod
    def _create_documentation_raw(cls):
        return """Create %s

        :response %s 200: Created
        :return %s: Current created object
        """

    def update(self, **kwargs):

        # todo deeply check unchanged
        unchanged_list = []
        for key, value in kwargs.items():
            if value == self.UNCHANGED:
                unchanged_list.append(key)
        for key in unchanged_list:
            del kwargs[key]

        base_kwargs, many_to_many_kwargs, _ = self.__class__._clean_model_data_kwargs(on_update=True, **kwargs)
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

    @classmethod
    def _update_documentation_params(cls):
        return stringcase.titlecase(cls.class_name()), cls.class_name(), cls.class_name()

    @classmethod
    def _update_documentation_raw(cls):
        return """Edit %s

        :response %s 200: Edited
        :return %s: Current edited object
        """

    def remove(self) -> dict:
        temp = self.to_dict()
        self.delete()
        return temp

    @classmethod
    def _remove_documentation_params(cls):
        return stringcase.titlecase(cls.class_name()), cls.class_name(), cls.class_name()

    @classmethod
    def _remove_documentation_raw(cls):
        return """Delete %s

        :response %s 200: Deleted
        :return %s: Deleted object
        """

    @classmethod
    def update_properties(cls) -> Dict[str, Parameter]:
        from avishan.libraries.openapi3 import get_functions_properties
        data = dict(get_functions_properties(getattr(cls, 'update')))
        del data['self']
        return data

    @classmethod
    def search(cls, query_set: models.QuerySet, search_text: str = None) -> models.QuerySet:
        if search_text is None:
            return query_set
        result = cls.objects.none()
        for field in cls.get_fields():
            if isinstance(field, models.CharField):
                result = query_set.filter(**{f'{field.name}__icontains': search_text}) | result
        return result.distinct()

    @classmethod
    def create_or_update(cls, fixed_kwargs: dict, new_additional_kwargs: dict):
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

    def to_dict(self, exclude_list: List[Union[models.Field, str]] = ()) -> dict:
        """
        Convert object to dict
        :return:
        """
        from khayyam import JalaliDatetime, JalaliDate

        dicted = {}

        for field in self.get_full_fields():
            if (field not in self.to_dict_private_fields and field.name not in self.to_dict_private_fields) and \
                    (field not in exclude_list and field.name not in exclude_list):
                value = self.get_data_from_field(field)
                if value is None:
                    dicted[field.name] = None
                elif isinstance(field, models.DateField):
                    if get_avishan_config().USE_DATETIME_DICT:
                        if value is None:
                            dicted[field.name] = {}
                        if get_avishan_config().USE_JALALI_DATETIME:
                            if isinstance(field, models.DateTimeField):
                                value = JalaliDatetime(value)
                            else:
                                value = JalaliDate(value)

                        if value is not None:
                            dicted[field.name] = {
                                'year': value.year,
                                'month': value.month,
                                'day': value.day
                            }
                            if isinstance(field, models.DateTimeField):
                                dicted[field.name]['hour'] = value.hour
                                dicted[field.name]['minute'] = value.minute
                                dicted[field.name]['second'] = value.second
                                dicted[field.name]['microsecond'] = value.microsecond
                    else:
                        if value is None:
                            dicted[field.name] = None
                        elif get_avishan_config().USE_JALALI_DATETIME:
                            if isinstance(field, models.DateTimeField):
                                format_string = get_avishan_config().DATETIME_STRING_FORMAT
                                dicted[field.name] = JalaliDatetime(value)
                            else:
                                format_string = get_avishan_config().DATE_STRING_FORMAT
                                dicted[field.name] = JalaliDate(value)
                            dicted[field.name] = dicted[field.name].strftime(format_string)
                        else:
                            if isinstance(field, models.DateTimeField):
                                dicted[field.name] = value.strftime(get_avishan_config().DATETIME_STRING_FORMAT)
                            else:
                                dicted[field.name] = value.strftime(get_avishan_config().DATE_STRING_FORMAT)

                elif isinstance(field, (models.OneToOneField, models.ForeignKey)):
                    dicted[field.name] = value.to_dict()
                elif isinstance(field, models.ManyToManyField):
                    dicted[field.name] = [item.to_dict() for item in value.all()]
                elif isinstance(value, datetime.time):
                    dicted[field.name] = {
                        'hour': value.hour, 'minute': value.minute, 'second': value.second,
                        'microsecond': value.microsecond
                    }
                else:
                    dicted[field.name] = value

        return dicted

    @classmethod
    def _clean_model_data_kwargs(cls, force_write_on: List[str] = (), on_update: bool = False, **kwargs):
        from avishan.exceptions import ErrorMessageException
        base_kwargs = {}
        many_to_many_kwargs = {}

        if 'is_api' in current_request.keys() and not current_request['is_api']:
            kwargs = cls._clean_form_post(kwargs)

        for field in cls.get_full_fields():
            """Check exists"""
            if field.name not in force_write_on and cls.is_field_readonly(field):
                continue

            if cls.is_field_required(field) and not on_update and field.name not in kwargs.keys():
                raise ErrorMessageException(AvishanTranslatable(
                    EN=f'Field {field.name} not found in object {cls.class_name()}, and it\'s required.',
                ))

            elif field.name not in kwargs.keys():
                continue

            """Read data part"""
            if isinstance(field, (models.OneToOneField, models.ForeignKey)):
                if isinstance(kwargs[field.name], models.Model):
                    base_kwargs[field.name] = kwargs[field.name]
                else:
                    if kwargs[field.name] == {'id': 0} or kwargs[field.name] is None:
                        base_kwargs[field.name] = None
                    else:
                        if field.related_model == TranslatableChar:
                            if isinstance(kwargs[field.name], dict):
                                en = kwargs[field.name].get('en', None)
                                fa = kwargs[field.name].get('fa', None)
                            elif isinstance(kwargs[field.name], str):
                                en = kwargs[field.name]
                                fa = kwargs[field.name]
                            else:
                                en = 'NOT TRANSLATED'
                                fa = 'NOT TRANSLATED'
                            base_kwargs[field.name] = TranslatableChar.create(en=en, fa=fa)
                        else:
                            base_kwargs[field.name] = field.related_model.get_from_dict(kwargs[field.name])
            elif isinstance(field, models.ManyToManyField):
                many_to_many_kwargs[field.name] = []
                for input_item in kwargs[field.name]:
                    if isinstance(input_item, models.Model):
                        item_object = input_item
                    else:
                        item_object = field.related_model.get_from_dict(input_item)
                    many_to_many_kwargs[field.name].append(item_object)
            else:
                base_kwargs[field.name] = cls.cast_field_data(kwargs[field.name], field)

        try:
            added_related_model_names = [item.class_snake_case_name() for item in cls.admin_related_models()]
        except:
            added_related_model_names = []
        after_creation = []
        if not on_update:
            for related_name in added_related_model_names:
                if related_name not in kwargs.keys():
                    continue
                related_model = AvishanModel.get_model_by_snake_case_name(related_name)
                for related_model_field in related_model.get_full_fields():
                    if isinstance(related_model_field, models.ForeignKey):
                        if related_model_field.related_model == cls:
                            target_related_field = related_model_field
                after_creation.append({
                    'created_for_field': target_related_field,
                    'target_objects': kwargs[related_name],
                    'target_model': related_model
                })
        return base_kwargs, many_to_many_kwargs, after_creation

    @classmethod
    def _clean_form_post(cls, kwargs: dict) -> dict:
        output = {}
        try:
            added_related_model_names = [item.class_snake_case_name() for item in cls.admin_related_models()]
        except:
            added_related_model_names = []

        for related_name in added_related_model_names:
            related_name_pack = []
            for key, value in kwargs.items():
                if key.startswith(related_name):
                    related_name_pack.append(key)

            if len(related_name_pack) == 0:
                continue
            kwargs[related_name] = []
            if isinstance(kwargs[related_name_pack[0]], str):
                kwargs[related_name].append({})
                for esme in related_name_pack:
                    kwargs[related_name][0][esme[len(related_name):]] = kwargs[esme]
            else:
                for i in range(kwargs[related_name_pack[0]].__len__()):
                    kwargs[related_name].append({})
                for key in related_name_pack:
                    for i, final_pack in enumerate(kwargs[related_name]):
                        final_pack[key[len(related_name):]] = kwargs[key][i]
            for key in related_name_pack:
                del kwargs[key]

        for key, value in kwargs.items():
            output[key] = value

        return output

    @classmethod
    def cast_field_data(cls, data, field: models.Field):

        if data is None:
            return None

        if isinstance(field, (models.CharField, models.TextField)):
            cast_class = str
        elif isinstance(field, (models.IntegerField, models.AutoField)):
            cast_class = int
        elif isinstance(field, models.FloatField):
            cast_class = float
        elif isinstance(field, models.TimeField):
            raise NotImplementedError('AvishanModel.cast_field_data for models.TimeField')
        elif isinstance(field, models.DateTimeField) and not isinstance(data, datetime.datetime):
            cast_class = datetime.datetime
        elif isinstance(field, models.DateField) and not isinstance(data, datetime.date):
            cast_class = datetime.date
        elif isinstance(field, models.BooleanField):
            cast_class = bool
        elif isinstance(field, (models.ManyToManyField, models.ForeignKey)):
            cast_class = field.related_model
        else:
            return data

        return cls.cast_type_data(cast_class, data)

    @classmethod
    def cast_type_data(cls, cast_class, data):
        from khayyam import JalaliDatetime

        format_string = get_avishan_config().DATETIME_STRING_FORMAT if \
            cast_class is datetime.datetime else \
            get_avishan_config().DATE_STRING_FORMAT

        if isinstance(cast_class, AvishanModel):
            if not isinstance(data, dict):
                raise ValueError('Relational args should contain dict with id or other unique values so that db can '
                                 'find corresponding object')
            output = cast_class.get_from_dict(data)
        elif cast_class in [datetime.datetime, datetime.date]:
            if isinstance(data, dict):
                if settings.USE_TZ:
                    data['tzinfo'] = pytz.timezone(settings.TIME_ZONE)

                if get_avishan_config().USE_JALALI_DATETIME:
                    output = JalaliDatetime(**data).todatetime() if \
                        cast_class is datetime.datetime else \
                        JalaliDatetime(**data).todate()
                else:
                    output = datetime.datetime(**data)
                    if cast_class is datetime.date:
                        output = output.date()
            elif isinstance(data, str):
                if get_avishan_config().USE_JALALI_DATETIME:
                    output = JalaliDatetime.strptime(data, format_string).todatetime()
                    if settings.USE_TZ:
                        output = output.replace(tzinfo=pytz.timezone(settings.TIME_ZONE))
                    if cast_class is datetime.date:
                        output = output.date()
                else:
                    output = datetime.datetime.strptime(data, format_string)
                    if settings.USE_TZ:
                        output = output.replace(tzinfo=pytz.timezone(settings.TIME_ZONE))
                    if cast_class is datetime.date:
                        output = output.date()
            else:
                raise ValueError('Cannot parse datetime, supported types are dict (containing year, month, .etc) or str'
                                 f' (with format "{format_string}")')
        else:
            output = cast_class(data)

        return output

    @classmethod
    def get_from_dict(cls, input_dict: dict) -> 'AvishanModel':
        """Converts dict object to Model"""

        """Shortcut for id"""
        if 'id' in input_dict.keys():
            return cls.get(id=input_dict['id'])

        """Usually when unique or one-to-one relations provided, this can help"""
        return cls.get(**input_dict)

    # todo 0.2.2: check None amount for choice added fields
    def get_data_from_field(self, field: models.Field):
        from avishan.exceptions import ErrorMessageException
        if field.choices is not None:
            for k, v in field.choices:
                if k == self.__getattribute__(field.name):
                    return v
            raise ErrorMessageException(AvishanTranslatable(
                EN=f'Incorrect Data entered for field {field.name} in model {self.class_name()}',
                FA=f'اطلاعات نامعتبر برای فیلد {field.name} مدل {self.class_name()}'
            ))

        if isinstance(field, models.ManyToManyField):
            return self.__getattribute__(field.name).all()

        return self.__getattribute__(field.name)

    @staticmethod
    def get_sum_on_field(query_set: models.QuerySet, field_name: str) -> int:
        from django.db.models import Sum
        total = query_set.aggregate(Sum(field_name))[field_name + "__sum"]
        if total:
            return total
        return 0

    @classmethod
    def chayi_ignore_serialize_field(cls, field: models.Field) -> bool:
        return cls.is_field_readonly(field)


class BaseUser(AvishanModel):
    """
    Avishan user object. Name changed to "BaseUser" instead of "User" to make this model name available for app models.
    """

    """Only active users can use system. This field checks on every request"""
    is_active = models.BooleanField(default=True, blank=True, help_text='Checks if user can use system')
    language = models.CharField(max_length=255, default=AvishanConfigFather.LANGUAGES.EN,
                                help_text='Language for user, using 2 words ISO standard: EN, FA, AR')
    date_created = models.DateTimeField(auto_now_add=True, help_text='Date user joined system')

    to_dict_private_fields = [date_created, 'id', is_active]

    django_admin_list_display = ['__str__', 'id', is_active, language, date_created]
    django_admin_list_filter = [language, is_active]

    @classmethod
    def create(cls) -> 'BaseUser':
        return super().create(
            language=get_avishan_config().NEW_USERS_LANGUAGE
            if get_avishan_config().NEW_USERS_LANGUAGE is not None
            else get_avishan_config().LANGUAGE
        )

    def add_to_user_group(self, user_group: 'UserGroup') -> 'UserUserGroup':
        return user_group.add_user_to_user_group(self)

    def __str__(self):
        if hasattr(self, 'user'):
            return str(self.user)
        return super().__str__()


class UserGroup(AvishanModel):
    """
    Every user most have at least one user group. User group controls it's member's overall activities. Every user have
    an models.authentication.UserUserGroup to manage it's group membership.
    """

    """Unique titles for groups. examples: Customer, User, Driver, Admin, Supervisor"""
    title = models.CharField(max_length=255, unique=True,
                             help_text='Project specific groups, like "driver", "customer"')
    token_valid_seconds = models.BigIntegerField(default=30 * 60, blank=True, help_text='Token valid seconds')

    to_dict_private_fields = [
        token_valid_seconds,
        'id'
    ]
    django_admin_list_display = [title, token_valid_seconds]

    @classmethod
    def create(cls, title: str, token_valid_seconds: int) -> 'UserGroup':
        return super().create(title=title, token_valid_seconds=token_valid_seconds)

    def add_user_to_user_group(self, base_user: BaseUser) -> 'UserUserGroup':
        """
        Create UUG or return it if available
        """
        try:
            return UserUserGroup.objects.get(
                base_user=base_user,
                user_group=self
            )
        except UserUserGroup.DoesNotExist:
            return UserUserGroup.objects.create(
                user_group=self,
                base_user=base_user
            )

    def __str__(self):
        return self.title


class UserUserGroup(AvishanModel):
    """
    Link between user and user group. Recommended object for addressing user and system models. It contains user group
    and you can distinguish between multiple user accounts.

    Token objects will contain address to this object, for having multiple-role login/logout without any interrupts.
    """

    """
    Uniqueness will be guaranteed for each user and an user group programmatically. Using database UNIQUE postponed for 
    lack of reliability on django Meta unique_together. 
    """
    # todo 0.2.1: raise appropriate exception for exceeding unique rule here.
    base_user = models.ForeignKey(BaseUser, on_delete=models.CASCADE, related_name='user_user_groups',
                                  help_text='BaseUser object side')
    user_group = models.ForeignKey(UserGroup, on_delete=models.CASCADE, related_name='user_user_groups',
                                   help_text='UserGroup object side')
    date_created = models.DateTimeField(auto_now_add=True, help_text='Date BaseUser added to this UserGroup')
    """
    Each token have address to models.authentication.UserUserGroup object. If this fields become false, user cannot use 
    system with this role. "is_active" field on models.authentication.BaseUser will not override on this field. 
    """
    is_active = models.BooleanField(default=True, blank=True, help_text='Is BaseUser active with this UserGroup')

    django_admin_list_display = [base_user, user_group, date_created]
    django_admin_list_filter = [user_group]
    django_admin_raw_id_fields = [base_user]
    to_dict_private_fields = [date_created, is_active]

    @classmethod
    def create(cls, user_group: UserGroup, base_user: BaseUser = None) -> 'UserUserGroup':
        if base_user is None:
            base_user = BaseUser.create()
        return super().create(user_group=user_group, base_user=base_user)

    @property
    def last_used(self) -> Optional[datetime.datetime]:
        """
        Last used datetime. it will caught throw user devices. If never used, returns None
        """
        dates = []
        if hasattr(self, 'emailpasswordauthenticate'):
            dates.append(self.emailpasswordauthenticate.last_used)
        if hasattr(self, 'phonepasswordauthenticate'):
            dates.append(self.phonepasswordauthenticate.last_used)

        if len(dates) == 0:
            return None
        return max(dates)

    @property
    def last_login(self) -> Optional[datetime.datetime]:
        """
        Last login comes from this user user group authorization types.
        """
        dates = []
        if hasattr(self, 'emailpasswordauthenticate'):
            dates.append(self.emailpasswordauthenticate.last_login)
        if hasattr(self, 'phonepasswordauthenticate'):
            dates.append(self.phonepasswordauthenticate.last_login)

        if len(dates) == 0:
            return None
        return max(dates)

    def check_is_active(self) -> bool:
        """Summary activation check

        :return: Is User active or not
        """
        if self.is_active:
            return self.base_user.is_active
        return False

    def __str__(self):
        return f'{self.base_user} - {self.user_group}'


class Identifier(AvishanModel):
    class Meta:
        abstract = True

    key = models.CharField(max_length=255, unique=True, help_text='Unique value of target data')

    django_admin_list_display = [key]
    django_admin_search_fields = [key]
    to_dict_private_fields = ['id']

    @classmethod
    def create(cls, key: str):
        """

        :param str key: Target key
        """
        return super().create(key=cls.validate_signature(key))

    @classmethod
    def get_or_create(cls, key: str):
        try:
            return cls.get(key=key)
        except cls.DoesNotExist:
            return cls.create(key=key)

    @classmethod
    def get(cls, avishan_raise_400: bool = False, **kwargs):
        kwargs['key'] = cls.validate_signature(kwargs['key'])
        return super().get(avishan_raise_400, **kwargs)

    def update(self, key: str):
        return super().update(key=self.validate_signature(key))

    @classmethod
    def filter(cls, **kwargs):
        if 'key' in kwargs.keys():
            kwargs['key'] = cls.validate_signature(kwargs['key'])
        return super().filter(**kwargs)

    @staticmethod
    def validate_signature(key: str) -> str:
        return key

    def __str__(self):
        return self.key


class Email(Identifier):

    def send_mail(self, subject: str, message: str, html_message: str = None):
        from avishan.exceptions import ErrorMessageException
        from avishan.libraries.mailgun.functions import send_mail as mailgun_send_mail

        if get_avishan_config().MAILGUN_EMAIL_ENABLE:
            mailgun_send_mail(recipient_list=[self.key], subject=subject, message=message)
        elif get_avishan_config().DJANGO_SMTP_EMAIL_ENABLE:
            self.send_bulk_mail(subject, message, [self.key], html_message)
        else:
            raise ErrorMessageException(AvishanTranslatable(
                EN='Email Provider not found. Enable in "Email Providers" avishan config section'
            ))

    @staticmethod
    def send_bulk_mail(subject: str, message: str, recipient_list: List[str], html_message: str = None):
        from django.core.mail import send_mail
        if html_message is not None:
            send_mail(subject, message, get_avishan_config().DJANGO_SMTP_SENDER_ADDRESS, recipient_list, html_message)
        else:
            send_mail(subject, message, get_avishan_config().DJANGO_SMTP_SENDER_ADDRESS, recipient_list)

    @staticmethod
    def validate_signature(key: str) -> str:
        return key.lower().strip()


class Phone(Identifier):
    @staticmethod
    def send_bulk_sms():
        pass  # todo

    def send_sms(self, text_body: str = None, **kwargs):
        from avishan.exceptions import ErrorMessageException
        from avishan.libraries.kavenegar import send_template_sms, send_raw_sms

        if get_avishan_config().KAVENEGAR_SMS_ENABLE:
            if 'template' in kwargs.keys():
                send_template_sms(
                    phone=self,
                    template_name=kwargs['template'],
                    token=kwargs.get('token'),
                    token2=kwargs.get('token2'),
                    token3=kwargs.get('token3')
                )
            else:
                send_raw_sms(
                    phone=self,
                    text=text_body
                )
        else:
            raise ErrorMessageException(AvishanTranslatable(
                EN='SMS Provider not found. Enable in "SMS Providers" avishan config section'
            ))

    def send_verification_sms(self, code: str, template: str = get_avishan_config().KAVENEGAR_DEFAULT_TEMPLATE):
        from avishan.exceptions import ErrorMessageException

        if get_avishan_config().KAVENEGAR_SMS_ENABLE:
            self.send_sms(
                template=template,
                token=code
            )
        else:
            raise ErrorMessageException(AvishanTranslatable(
                EN='SMS Provider not found. Enable in "SMS Providers" avishan config section'
            ))

    @staticmethod
    def validate_signature(phone: str, country_data: dict = None) -> str:
        """
        https://en.wikipedia.org/wiki/List_of_mobile_telephone_prefixes_by_country
        # each telecom numbers

        minimum number of digits for a mobile number is 4 [Country:Saint Helena]
        Max digits for a mobile number is 13 [Country: Austria]
        \+(9[976]\d|8[987530]\d|6[987]\d|5[90]\d|42\d|3[875]\d|
        2[98654321]\d|9[8543210]|8[6421]|6[6543210]|5[87654321]|
        4[987654310]|3[9643210]|2[70]|7|1)\d{1,14}$
        """
        if country_data is None:
            country_data = get_avishan_config().get_country_mobile_numbers_data()[0]

        # remove all non-numbers characters
        result = ''.join(re.findall('[0-9]', phone))
        # now match with validation regex
        # todo check for 09 programmatically
        result = re.sub(f'({country_data["dialing_code"]}|00{country_data["dialing_code"]})?(0)?([0-9]*)', r'\3',
                        result)
        if len(result) < 10:
            raise ValueError(f'Smaller Number Extracted: {result}')
        elif len(result) != 10:
            raise ValueError(f'Bigger Number Extracted: {result}')

        temp = (some for some in country_data['mobile_providers'].values())
        prefixes = []
        for item in temp:
            prefixes += item

        if not result.startswith(tuple(prefixes)):
            raise ValueError('Invalid Prefix')

        return f"00{country_data['dialing_code']}" + result


class AuthenticationVerification(AvishanModel):
    code = models.CharField(max_length=255)
    date_created = models.DateTimeField(auto_now_add=True)
    tried_codes = models.TextField(default="", blank=True)  # separate by |

    to_dict_private_fields = [code, tried_codes]

    @classmethod
    def create(cls, code_length: int, code_domain: str = string.ascii_letters) -> 'AuthenticationVerification':
        return super().create(
            code=cls._code_generator(code_length, code_domain)
        )

    def check_code(self, entered_code: str, valid_seconds: int) -> bool:
        from avishan.exceptions import ErrorMessageException

        if (timezone.now() - self.date_created).total_seconds() > valid_seconds:
            self.remove()
            raise ErrorMessageException(AvishanTranslatable(
                EN='Code Expired',
                FA='کد منقضی شده است'
            ))

        if self.code != entered_code:
            self.tried_codes += f"{entered_code}\n"
            self.save()
            return False

        self.remove()
        return True

    @classmethod
    def _code_generator(cls, code_length: int, code_domain: str) -> str:
        return ''.join(random.choice(code_domain) for _ in range(code_length))


class AuthenticationType(AvishanModel):
    class Meta:
        abstract = True

    user_user_group = models.OneToOneField(UserUserGroup, on_delete=models.CASCADE, related_name='%(class)s',
                                           help_text='Target UserUserGroup')
    last_used = models.DateTimeField(blank=True, null=True, help_text='Last time user sent request')
    last_login = models.DateTimeField(blank=True, null=True, help_text='Last time user logged in')
    last_logout = models.DateTimeField(blank=True, null=True, help_text='Last time user logged out')
    is_active = models.BooleanField(default=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)

    export_ignore = True

    django_admin_raw_id_fields = [user_user_group]
    django_admin_list_display = ['key', user_user_group, last_used, last_login, last_logout]
    django_admin_list_filter = [user_user_group]
    django_admin_search_fields = ['key']
    to_dict_private_fields = [last_used, last_login, last_logout, date_created, is_active]

    @classmethod
    def direct_callable_methods(cls):
        return super().direct_callable_methods() + [
            DirectCallable(
                model=cls,
                target_name='login',
                response_json_key=cls.class_snake_case_name(),
                method=DirectCallable.METHOD.POST,
                authenticate=False
            ),
            DirectCallable(
                model=cls,
                target_name='register',
                response_json_key=cls.class_snake_case_name(),
                method=DirectCallable.METHOD.POST,
                authenticate=False
            )
        ]

    @classmethod
    def register(cls, **kwargs) -> Union[
        'EmailKeyValueAuthentication',
        'PhoneKeyValueAuthentication',
        'EmailOtpAuthentication',
        'PhoneOtpAuthentication',
        'VisitorKeyAuthentication'
    ]:
        raise NotImplementedError()

    @classmethod
    def login(cls, **kwargs) -> Union[
        'EmailKeyValueAuthentication',
        'PhoneKeyValueAuthentication',
        'EmailOtpAuthentication',
        'PhoneOtpAuthentication',
        'VisitorKeyAuthentication'
    ]:
        raise NotImplementedError()

    @classmethod
    def find(cls, key: Union[Email, Phone, str], user_group: UserGroup) -> Optional[Union[
        'EmailKeyValueAuthentication',
        'PhoneKeyValueAuthentication',
        'EmailOtpAuthentication',
        'PhoneOtpAuthentication',
        'VisitorKeyAuthentication'
    ]]:
        """Finds item for each key+uug"""
        try:
            return cls.get(
                key=key,
                user_user_group__user_group=user_group
            )
        except cls.DoesNotExist:
            return None
        except cls.MultipleObjectsReturned:
            raise AuthException(error_kind=AuthException.MULTIPLE_CONNECTED_ACCOUNTS)

    @classmethod
    def _related_key_model(cls):
        """Returns target model for key, if available, else None"""
        field: models.ForeignKey = cls.get_field('key')
        if not field:
            return None
        return field.related_model

    @classmethod
    def _register(cls, key: Union[Email, Phone, str], user_user_group: UserUserGroup,
                  **create_added_kwargs) -> Union[
        'EmailKeyValueAuthentication',
        'PhoneKeyValueAuthentication',
        'EmailOtpAuthentication',
        'PhoneOtpAuthentication',
        'VisitorKeyAuthentication'
    ]:
        from avishan.exceptions import AuthException

        if isinstance(key, str) and cls._related_key_model():
            try:
                key = cls._related_key_model().get(key=key)
            except cls._related_key_model().DoesNotExist:
                key = cls._related_key_model().create(key)

        if cls.find(key, user_user_group.user_group):
            raise AuthException(AuthException.DUPLICATE_AUTHENTICATION_IDENTIFIER)

        creation_dict = {
            **{
                'user_user_group': user_user_group,
                'key': key,
            },
            **create_added_kwargs
        }

        return cls.create(**creation_dict)

    @classmethod
    def _login(cls, key: Union[Email, Phone, str], user_group: UserGroup, **kwargs) -> Union[
        'EmailKeyValueAuthentication',
        'PhoneKeyValueAuthentication',
        'EmailOtpAuthentication',
        'PhoneOtpAuthentication',
        'VisitorKeyAuthentication'
    ]:
        from avishan.exceptions import AuthException

        found_object: Union[
            'EmailKeyValueAuthentication',
            'PhoneKeyValueAuthentication',
            'EmailOtpAuthentication',
            'PhoneOtpAuthentication',
            'VisitorKeyAuthentication'
        ] = cls.find(key, user_group)
        if not found_object:
            raise AuthException(AuthException.ACCOUNT_NOT_FOUND)

        kwargs['found_object'] = found_object
        kwargs['submit_login'] = True

        cls._login_before_submit_actions(kwargs)

        if kwargs['submit_login']:
            found_object._submit_login()
        return found_object

    @classmethod
    def _login_before_submit_actions(cls, data: dict):
        """Before login check space"""
        pass

    def _submit_login(self):
        if not self.is_active:
            raise ErrorMessageException(AvishanTranslatable(
                EN='Authentication types deactivated, try other types',
                FA='این نوع احراز هویت غیرفعال شده است، لطفا نوع دیگری را امتحان کنید'
            ))
        if not self.user_user_group.check_is_active():
            raise ErrorMessageException(AvishanTranslatable(
                EN='User deactivated',
                FA='کاربر غیرفعال شده‌است'
            ))
        self.last_login = timezone.now()
        self.last_used = None
        self.last_logout = None
        self.save()
        self._populate_current_request()

    def _submit_logout(self):
        self.last_logout = timezone.now()
        self.save()
        current_request['add_token'] = False

    def _populate_current_request(self):
        current_request['base_user'] = self.user_user_group.base_user
        current_request['user_group'] = self.user_user_group.user_group
        current_request['user_user_group'] = self.user_user_group
        current_request['authentication_object'] = self
        if current_request['language'] is None:
            current_request['language'] = self.user_user_group.base_user.language
        current_request['add_token'] = True


class VerifiableAuthenticationType(AuthenticationType):
    class Meta:
        abstract = True

    date_verified = models.DateTimeField(default=None, null=True, blank=True)
    verification = models.OneToOneField(AuthenticationVerification, on_delete=models.SET_NULL, null=True, blank=True)

    to_dict_private_fields = [verification, 'last_used', 'last_login', 'last_logout', 'date_created', 'is_active']

    @classmethod
    def direct_callable_methods(cls):
        return super().direct_callable_methods() + [
            DirectCallable(
                model=cls,
                target_name='start_verification',
                authenticate=False
            ),
            DirectCallable(
                model=cls,
                target_name='check_verification',
                authenticate=False,
                method=DirectCallable.METHOD.POST,
                dismiss_request_json_key=True
            )
        ]

    def must_verify(self) -> bool:
        if getattr(get_avishan_config(), stringcase.constcase(self.class_name()) + '_VERIFICATION_REQUIRED'):
            return True
        return self.date_verified is not None

    def start_verification(self):
        self: Union[
            EmailKeyValueAuthentication, PhoneKeyValueAuthentication, EmailOtpAuthentication, PhoneOtpAuthentication]
        if not getattr(get_avishan_config(), stringcase.constcase(self.class_name()) + '_VERIFICATION_REQUIRED'):
            return
        if self.verification:
            if (timezone.now() - self.verification.date_created).total_seconds() < getattr(
                    get_avishan_config(), stringcase.constcase(self.class_name()) + '_VERIFICATION_CODE_GAP_SECONDS'):
                raise ErrorMessageException(AvishanTranslatable(
                    EN='Code created recently, try again later',
                    FA='کد به تازگی ایجاد شده است، کمی بعد تلاش کنید'
                ))
            else:
                self.verification.remove()

        self.date_verified = None
        self.verification = AuthenticationVerification.create(
            code_length=getattr(get_avishan_config(),
                                stringcase.constcase(self.class_name()) + '_VERIFICATION_CODE_LENGTH'),
            code_domain=getattr(get_avishan_config(),
                                stringcase.constcase(self.class_name()) + '_VERIFICATION_CODE_DOMAIN')
        )
        self.save()

        if self._related_key_model() is Email:
            message = getattr(get_avishan_config(), stringcase.snakecase(self.class_name()) +
                              '_verification_body')(self)
            html_message = getattr(get_avishan_config(), stringcase.snakecase(self.class_name()) +
                                   '_verification_html_body')(self)
            if message:
                message = message.format(code=self.verification.code)
            elif html_message:
                html_message = html_message.format(code=self.verification.code)
            self.key.send_mail(
                subject=getattr(get_avishan_config(), stringcase.snakecase(self.class_name()) +
                                '_verification_subject')(self),
                message=message,
                html_message=html_message
            )
        elif self._related_key_model() is Phone:
            self.key.send_verification_sms(
                code=self.verification.code
            )
        else:
            raise NotImplementedError()

    def check_verification(self, code: str):
        from avishan.exceptions import ErrorMessageException

        if not self.verification:
            raise ErrorMessageException(AvishanTranslatable(
                EN='Verification not started',
                FA='اعتبارسنجی آغاز نشده است'
            ))
        if not self.verification.check_code(
                entered_code=code,
                valid_seconds=getattr(get_avishan_config(), stringcase.constcase(self.class_name()) +
                                                            '_VERIFICATION_CODE_VALID_SECONDS')
        ):
            raise ErrorMessageException(AvishanTranslatable(
                EN='Incorrect Code',
                FA='کد اشتباه'
            ))
        self.date_verified = timezone.now()
        self.save()

        self._successful_verification_post_actions()

    @classmethod
    def _login_before_submit_actions(cls, data: dict):
        super()._login_before_submit_actions(data)
        found_object: cls = data['found_object']
        if getattr(get_avishan_config(), stringcase.constcase(cls.class_name()) + '_VERIFICATION_REQUIRED') \
                and found_object.date_verified is None:
            raise ErrorMessageException(AvishanTranslatable(
                EN='Account not verified',
                FA='حساب تایید نشده است'
            ))

    def _successful_verification_post_actions(self):
        """If successful verification"""
        pass

    @classmethod
    def register(cls, **kwargs) -> Union[
        'EmailKeyValueAuthentication',
        'PhoneKeyValueAuthentication',
        'EmailOtpAuthentication',
        'PhoneOtpAuthentication',
        'VisitorKeyAuthentication'
    ]:
        raise NotImplementedError()

    @classmethod
    def login(cls, **kwargs) -> Union[
        'EmailKeyValueAuthentication',
        'PhoneKeyValueAuthentication',
        'EmailOtpAuthentication',
        'PhoneOtpAuthentication',
        'VisitorKeyAuthentication'
    ]:
        raise NotImplementedError()


class KeyValueAuthentication(VerifiableAuthenticationType):
    class Meta:
        abstract = True

    hashed_password = models.CharField(max_length=255, blank=True, null=True)
    change_password_token = models.CharField(max_length=255, blank=True, null=True, default=None)
    change_password_date = models.DateTimeField(max_length=255, blank=True, null=True, default=None)

    to_dict_private_fields = [hashed_password, 'verification', 'last_used', 'last_login', 'last_logout', 'date_created',
                              'is_active', change_password_token, change_password_date]

    @classmethod
    def register(cls, key: Union[Email, Phone], user_user_group: UserUserGroup, password: str = None,
                 verify_now: bool = False, add_token: bool = False) -> \
            Union['EmailKeyValueAuthentication', 'PhoneKeyValueAuthentication']:

        created = cls._register(
            key=key,
            user_user_group=user_user_group
        )

        if len(password.strip()) == 0:
            password = None
        if password:
            created.set_password(password)

        if verify_now:
            created.start_verification()

        if add_token:
            created.login(
                key=key,
                user_group=user_user_group.user_group,
                password=password
            )
        return created

    @classmethod
    def login(cls, key: Union[Email, Phone], user_group: UserGroup, password: str) -> \
            Union['EmailKeyValueAuthentication', 'PhoneKeyValueAuthentication']:
        return cls._login(key=key, user_group=user_group, password=password)

    @classmethod
    def find(cls, key: Union[Email, Phone], user_group: UserGroup) \
            -> Optional[Union['EmailKeyValueAuthentication', 'PhoneKeyValueAuthentication']]:
        return super().find(key, user_group)

    def set_password(self, password: str):
        self.hashed_password = self._hash_password(password)
        self.save()

    def change_password(self, old_password: str, new_password: str):
        if not self.hashed_password:
            raise AuthException(error_kind=AuthException.PASSWORD_NOT_FOUND)
        if not self._check_password(old_password):
            raise AuthException(error_kind=AuthException.INCORRECT_PASSWORD)
        self.set_password(new_password)

    @classmethod
    def reset_password_start(cls, key: Union[Email, Phone], user_group: UserGroup):
        found = cls.find(key=key, user_group=user_group)

        """Account not found"""
        if not found:
            raise AuthException(AuthException.ACCOUNT_NOT_FOUND)

        """Check for gap seconds"""
        if found.change_password_token and (timezone.now() - found.change_password_date).total_seconds() < getattr(
                get_avishan_config(), stringcase.constcase(cls.class_name()) + '_RESET_PASSWORD_GAP_SECONDS'):
            raise ErrorMessageException('Reset password applied recently, please try later')

        """Do routine"""
        found._reset_password()

        """Sending Part"""
        if found._related_key_model() is Email:
            message = getattr(get_avishan_config(), stringcase.constcase(cls.class_name()) +
                              '_RESET_PASSWORD_BODY')
            html_message = getattr(get_avishan_config(), stringcase.constcase(cls.class_name()) +
                                   '_RESET_PASSWORD_HTML_BODY')
            if message:
                message = message.format(token=found.change_password_token)
            elif html_message:
                html_message = html_message.format(code=found.change_password_token)
            found.key.send_mail(
                subject=getattr(get_avishan_config(), stringcase.constcase(cls.class_name()) +
                                '_RESET_PASSWORD_SUBJECT'),
                message=message,
                html_message=html_message
            )
        elif found._related_key_model() is Phone:
            found.key.send_verification_sms(
                code=found.change_password_token,
                template=getattr(
                    get_avishan_config(), stringcase.constcase(cls.class_name()) + '_RESET_PASSWORD_SMS_TEMPLATE'
                )
            )
        else:
            raise NotImplementedError()

    @classmethod
    def reset_password_check(cls, key: Union[Email, Phone], user_group: UserGroup, token: str) -> bool:
        found = cls.find(key=key, user_group=user_group)

        """Account not found"""
        if not found:
            raise AuthException(AuthException.ACCOUNT_NOT_FOUND)

        if (timezone.now() - found.change_password_date).total_seconds() > getattr(
                get_avishan_config(), stringcase.constcase(cls.class_name()) + '_RESET_PASSWORD_VALID_SECONDS'
        ):
            raise ErrorMessageException('Reset password code expired, apply for a new one')

        return found.change_password_token == token

    @classmethod
    def reset_password_complete(cls, key: Union[Email, Phone], user_group: UserGroup, token: str, password: str):
        if not cls.reset_password_check(key, user_group, token):
            raise ErrorMessageException('Incorrect reset password code')
        found = cls.find(key, user_group)
        found._apply_reset_password(password)

    def _reset_password(self):
        self.hashed_password = None
        self.change_password_token = ''.join(
            random.choice(getattr(get_avishan_config(), stringcase.constcase(self.class_name()) +
                                  '_RESET_PASSWORD_TOKEN_DOMAIN')) for _ in
            range(getattr(get_avishan_config(), stringcase.constcase(self.class_name()) +
                          '_RESET_PASSWORD_TOKEN_LENGTH')))
        self.change_password_date = timezone.now()
        self.save()

    def _apply_reset_password(self, password: str):
        self.set_password(password)
        self.change_password_token = None
        self.change_password_date = None
        self.save()

    @staticmethod
    def _hash_password(password: str) -> str:
        """
        Hash entered password
        :param password:
        :return: hashed password in string
        """
        import bcrypt
        return bcrypt.hashpw(password.encode('utf8'), bcrypt.gensalt()).decode('utf8')

    def _check_password(self, password: str) -> bool:
        """
        compares password with hashed instance.
        :param password:
        :return: True if match
        """
        if not self.hashed_password:
            raise AuthException(error_kind=AuthException.PASSWORD_NOT_FOUND)
        import bcrypt
        return bcrypt.checkpw(password.encode('utf8'), self.hashed_password.encode('utf8'))

    @classmethod
    def _login_before_submit_actions(cls, data: dict):
        super()._login_before_submit_actions(data)
        if not data['found_object']._check_password(data['password']):
            raise AuthException(AuthException.INCORRECT_PASSWORD)


class EmailKeyValueAuthentication(KeyValueAuthentication):
    key = models.ForeignKey(Email, on_delete=models.CASCADE, related_name='key_value_authentications')


class PhoneKeyValueAuthentication(KeyValueAuthentication):
    key = models.ForeignKey(Phone, on_delete=models.CASCADE, related_name='key_value_authentications')


class OtpAuthentication(VerifiableAuthenticationType):
    class Meta:
        abstract = True

    def _successful_verification_post_actions(self):
        super()._successful_verification_post_actions()
        self._submit_login()

    @classmethod
    def register(cls, key: Union[Email, Phone], user_user_group: UserUserGroup, add_token: bool = False):
        created = cls._register(
            key=key,
            user_user_group=user_user_group
        )

        if add_token:
            created.login(
                key=key,
                user_group=user_user_group.user_group
            )

        return created

    @classmethod
    def login(cls, key: Union[Email, Phone], user_group: UserGroup):
        return cls._login(key=key, user_group=user_group)

    @classmethod
    def _login_before_submit_actions(cls, data: dict):
        super()._login_before_submit_actions(data)
        found_object: cls = data['found_object']
        found_object.verification = None
        found_object.date_verified = None
        found_object.save()
        data['submit_login'] = False
        found_object.start_verification()


class EmailOtpAuthentication(OtpAuthentication):
    key = models.ForeignKey(Email, on_delete=models.CASCADE, related_name='otp_authentications')


class PhoneOtpAuthentication(OtpAuthentication):
    key = models.ForeignKey(Phone, on_delete=models.CASCADE, related_name='otp_authentications')


class KeyAuthentication(AuthenticationType):
    class Meta:
        abstract = True

    key = models.CharField(max_length=255)

    @classmethod
    def create(cls, key: str, user_user_group: UserUserGroup):
        return super().create(
            key=key,
            user_user_group=user_user_group
        )

    @classmethod
    def register(cls, user_user_group: UserUserGroup):
        key = cls.generate_key()
        while True:
            try:
                cls.get(key=key)
                key = cls.generate_key()
            except cls.DoesNotExist:
                break

        data = {
            'user_user_group': user_user_group,
            'key': key,
        }

        return cls.objects.create(**data)

    @classmethod
    def login(cls, key: str, user_group: UserGroup):
        from avishan.exceptions import AuthException

        found_object: KeyAuthentication = cls.find(key, user_group)
        if not found_object:
            raise AuthException(AuthException.ACCOUNT_NOT_FOUND)

        found_object._submit_login()
        return found_object

    @classmethod
    def generate_key(cls) -> str:
        import secrets
        return secrets.token_urlsafe(
            getattr(get_avishan_config(), stringcase.constcase(cls.class_name()) + '_KEY_LENGTH'))


class VisitorKeyAuthentication(KeyAuthentication):
    pass


class File(AvishanModel):
    file = models.FileField(blank=True, null=True, help_text='File url')
    base_user = models.ForeignKey(BaseUser, on_delete=models.SET_NULL, null=True, blank=True, help_text='Uploaded by')
    date_created = models.DateTimeField(auto_now_add=True, help_text='Date uploaded')

    export_ignore = True

    django_admin_list_display = [file, base_user, date_created]
    django_admin_raw_id_fields = [base_user]

    def to_dict(self, exclude_list: List[Union[models.Field, str]] = ()) -> dict:
        return {
            'id': self.id,
            'file': self.file.url
        }


class Image(AvishanModel):
    file = models.ImageField(blank=True, null=True, help_text='Image url')
    base_user = models.ForeignKey(BaseUser, on_delete=models.SET_NULL, null=True, blank=True, help_text='Uploaded by')
    date_created = models.DateTimeField(auto_now_add=True, help_text='Date uploaded')

    export_ignore = True

    django_admin_list_display = [file, base_user, date_created]
    django_admin_raw_id_fields = [base_user]

    def __str__(self):
        try:
            return self.file.url
        except ValueError:
            return super().__str__()

    @classmethod
    def direct_callable_methods(cls) -> List[DirectCallable]:
        total = []
        for item in super().direct_callable_methods():
            total.append(item)
            if item.name == 'create':
                item.hide_in_redoc = True

        return total + [
            DirectCallable(
                model=cls,
                target_name='image_from_multipart_form_data_request',
                response_json_key='image',
                method=DirectCallable.METHOD.POST,
                dismiss_request_json_key=True
            )]

    @staticmethod
    def image_from_url(url: str) -> 'Image':
        from django.core.files import File

        name = url.split('/')[-1]
        if '.' not in name:
            name = url.split('/')[-2]

        image = Image.objects.create()
        image.file.save(name, File(open(url, 'rb')), save=True)

        image.save()
        return image

    def to_dict(self, exclude_list: List[Union[models.Field, str]] = ()) -> dict:
        return {
            'id': self.id,
            'file': self.file.url
        }

    @classmethod
    def image_from_in_memory_upload(cls, file: InMemoryUploadedFile) -> 'Image':
        from avishan.exceptions import ErrorMessageException
        if file is None:
            raise ErrorMessageException(AvishanTranslatable(
                EN='File not found',
                FA='فایل ارسال نشده است'
            ))

        created = Image.create(
            base_user=current_request['base_user']
        )
        created.file.save("uploaded_images/" + file.name, file, save=True)
        created.save()

        return created

    @classmethod
    def image_from_multipart_form_data_request(cls, name: str = 'file') -> 'Image':
        """Upload Image

        Upload image to server using "multipart/form-data".

        :param str? name: key in multipart form data
        :response Image 200: Saved
        """
        return cls.image_from_in_memory_upload(file=current_request['request'].FILES.get(name))


class RequestTrack(AvishanModel):
    # todo create it on request start, to use it in other places too
    view_name = models.CharField(max_length=255, blank=True, null=True, default="NOT_AVAILABLE")
    url = models.TextField(blank=True, null=True)
    status_code = models.IntegerField(null=True, blank=True)
    method = models.CharField(max_length=255, null=True, blank=True)
    json_unsafe = models.BooleanField(null=True, blank=True)
    is_api = models.BooleanField(null=True, blank=True)
    add_token = models.BooleanField(null=True, blank=True)
    user_user_group = models.ForeignKey(UserUserGroup, on_delete=models.SET_NULL, null=True, blank=True)
    request_data = models.TextField(null=True, blank=True)
    request_data_size = models.BigIntegerField(default=None, null=True, blank=True)
    request_headers = models.TextField(null=True, blank=True)
    response_data = models.TextField(null=True, blank=True)
    response_data_size = models.BigIntegerField(default=None, null=True, blank=True)
    start_time = models.DateTimeField(blank=True, null=True)
    end_time = models.DateTimeField(blank=True, null=True)
    total_execution_milliseconds = models.BigIntegerField(null=True, blank=True)
    view_execution_milliseconds = models.BigIntegerField(null=True, blank=True)
    authentication_type_class_title = models.CharField(max_length=255, blank=True, null=True)
    authentication_type_object_id = models.IntegerField(blank=True, null=True)

    django_admin_search_fields = [url]
    django_admin_list_display = [url, method, status_code, user_user_group, 'time', 'total_exec', 'view_exec']
    django_admin_list_filter = ['url']

    export_ignore = True

    def total_exec(self):
        return self.total_execution_milliseconds

    def view_exec(self):
        return self.view_execution_milliseconds

    def time(self):
        if not self.start_time:
            return self.start_time
        return self.start_time.strftime("%d/%m/%y %H:%M:%S.%f")

    def clean_url(self) -> str:
        return re.sub(r'(?x)/\d+.*', '/{id}', self.url)

    def __str__(self):
        return self.view_name


class RequestTrackException(AvishanModel):
    request_track = models.OneToOneField(RequestTrack, on_delete=models.CASCADE, related_name='exception')
    class_title = models.CharField(max_length=255, null=True, blank=True)
    args = models.TextField(null=True, blank=True)
    traceback = models.TextField(null=True, blank=True)

    django_admin_list_display = [request_track, class_title, args]
    django_admin_raw_id_fields = [request_track]

    export_ignore = True

    @classmethod
    def create(cls, request_track: RequestTrack, class_title: str, args: str,
               traceback: str) -> 'RequestTrackException':
        return super().create(
            request_track=request_track,
            class_title=class_title,
            args=args,
            traceback=traceback
        )


class TranslatableChar(AvishanModel):
    en = models.CharField(max_length=255, blank=True, null=True, default=None)
    fa = models.CharField(max_length=255, blank=True, null=True, default=None)

    export_ignore = True

    django_admin_list_display = [en, fa]

    @classmethod
    def create(cls, en: str = None, fa: str = None, auto: str = None) -> 'TranslatableChar':
        if en is not None:
            en = str(en)
            if len(en) == 0:
                en = None
        if fa is not None:
            fa = str(fa)
            if len(fa) == 0:
                fa = None
        return super().create(en=en, fa=fa)

    def to_dict(self, exclude_list: List[Union[models.Field, str]] = ()) -> Union[str, dict]:
        if current_request['language'] == 'all':
            return {
                'en': self.en,
                'fa': self.fa
            }
        return str(self)

    def __str__(self):
        try:
            return self.__getattribute__(current_request['language'].lower())
        except:
            return self.__getattribute__(get_avishan_config().LANGUAGE.lower())


class Activity(AvishanModel):
    title = models.CharField(max_length=255)
    user_user_group = models.ForeignKey(UserUserGroup, on_delete=models.CASCADE)
    request_track = models.ForeignKey(RequestTrack, on_delete=models.SET_NULL, null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    object_class = models.CharField(max_length=255, blank=True, null=True)
    object_id = models.BigIntegerField(default=None, null=True, blank=True)
    data = models.TextField(blank=True, null=True)

    django_admin_list_display = [user_user_group, title, data, object_class, object_id, date_created]
    django_admin_raw_id_fields = [user_user_group, request_track]

    export_ignore = True

    @classmethod
    def create(cls,
               title: str,
               object_class: str = None,
               object_id: int = None,
               data: str = None
               ) -> Optional['Activity']:
        """Creates object of :class:`Activity`

        :param str title: activity showing title
        :param str object_class: name of target class, defaults to None
        :param int object_id: target object, defaults to None
        :param str data: notes about activity, defaults to None
        :return Activity: created activity
        """
        request_track = current_request['request_track_object']
        user_user_group = current_request['user_user_group']
        if not request_track and not user_user_group:
            return
        return super().create(
            title=title,
            user_user_group=user_user_group if user_user_group else request_track.user_user_group,
            request_track=request_track,
            object_class=object_class,
            object_id=object_id,
            data=data
        )

    @classmethod
    def class_plural_name(cls) -> str:
        return 'Activities'

    def __str__(self):
        return self.title


class Country(AvishanModel):
    name = models.CharField(max_length=255)
    alpha_2_code = models.CharField(max_length=255)
    alpha_3_code = models.CharField(max_length=255)
    region = models.CharField(max_length=255)
    native_name = models.CharField(max_length=255, blank=True, null=True)
    numeric_code = models.CharField(max_length=255, unique=True)
    flag_url = models.CharField(max_length=255, blank=True, null=True)

    # noinspection PyPep8Naming
    @classmethod
    def create(cls,
               numericCode: str,
               name: str,
               alpha2Code: str,
               alpha3Code: str,
               region: str,
               nativeName: str = None,
               flag: str = None,
               **kwargs
               ):
        return super().create(
            numeric_code=numericCode,
            name=name,
            alpha_2_code=alpha2Code,
            alpha_3_code=alpha3Code,
            region=region,
            native_name=nativeName,
            flag_url=flag
        )

    # noinspection PyPep8Naming
    def update(self,
               name: str,
               alpha2Code: str,
               alpha3Code: str,
               region: str,
               nativeName: str = None,
               flag: str = None,
               **kwargs
               ):
        return super().update(
            name=name,
            alpha_2_code=alpha2Code,
            alpha_3_code=alpha3Code,
            region=region,
            native_name=nativeName,
            flag_url=flag
        )

    @classmethod
    def class_plural_name(cls) -> str:
        return 'Countries'
