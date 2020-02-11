import random
from typing import List, Type, Union, Tuple

import requests
from django.db.models import NOT_PROVIDED

from avishan import current_request
from avishan.misc import status
from avishan.misc.translation import AvishanTranslatable

import datetime
from typing import Optional

from avishan.misc.bch_datetime import BchDatetime
from django.db import models


class AvishanModel(models.Model):
    # todo 0.2.1: use manager or simply create functions here?
    # todo 0.2.0 relation on_delete will call our remove() ?
    class Meta:
        abstract = True

    """
    Models default settings
    """
    private_fields: List[Union[models.Field, str]] = []

    """
    Django admin default values. Set this for all inherited models
    """
    django_admin_date_hierarchy: Optional[str] = None
    django_admin_list_display: List[models.Field] = []
    django_admin_list_filter: List[models.Field] = []
    django_admin_list_max_show_all: int = 300
    django_admin_list_per_page: int = 100
    django_admin_raw_id_fields: List[models.Field] = []
    django_admin_readonly_fields: List[models.Field] = []
    django_admin_search_fields: List[models.Field] = []

    """
    CRUD functions
    """

    @classmethod
    def get(cls, avishan_to_dict: bool = False, avishan_raise_400: bool = False,
            **kwargs):
        from avishan.exceptions import ErrorMessageException
        # todo 0.2.1 compact, private, added properties
        if avishan_to_dict:
            return cls.get(avishan_to_dict=False, avishan_raise_400=avishan_raise_400, **kwargs).to_dict()

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
    def filter(cls, avishan_to_dict: bool = False, **kwargs):
        # todo show filterable fields on doc
        if avishan_to_dict:
            return [item.to_dict() for item in cls.filter(**kwargs)]

        if len(kwargs.items()) > 0:
            return cls.objects.filter(**kwargs)
        else:
            return cls.objects.all()

    @classmethod
    def all(cls, avishan_to_dict: bool = False):
        return cls.filter(avishan_to_dict=avishan_to_dict)

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

    def update(self, **kwargs):
        base_kwargs, many_to_many_kwargs, _ = self.__class__._clean_model_data_kwargs(**kwargs)
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

    def remove(self) -> dict:
        temp = self.to_dict()
        self.delete()
        return temp

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

        # todo 0.2.1: compact
        dicted = {}

        for field in self.get_full_fields():
            if (field not in self.private_fields and field.name not in self.private_fields) and \
                    (field not in exclude_list and field.name not in exclude_list):
                value = self.get_data_from_field(field)
                if value is None:
                    dicted[field.name] = None
                elif isinstance(field, models.DateField):
                    from avishan_config import AvishanConfig
                    try:
                        if AvishanConfig.USE_JALALI_DATETIME:
                            dicted[field.name] = BchDatetime(value).to_dict(full=True)
                        else:
                            if value is None:
                                dicted[field.name] = {}
                            else:
                                dicted[field.name] = {
                                    'year': value.year,
                                    'month': value.month,
                                    'day': value.day
                                }
                                if isinstance(field, models.DateTimeField):
                                    dicted[field.name] = {**{
                                        'hour': value.hour,
                                        'minute': value.minute,
                                        'second': value.second,
                                        'microsecond': value.microsecond
                                    }, **dicted[field.name]}
                    except:
                        dicted[field.name] = {}
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
    def _clean_model_data_kwargs(cls, on_update: bool = False, **kwargs):
        from avishan.exceptions import ErrorMessageException
        base_kwargs = {}
        many_to_many_kwargs = {}

        if 'is_api' in current_request.keys() and not current_request['is_api']:
            kwargs = cls._clean_form_post(kwargs)

        delete_list = []
        for key, value in kwargs.items():
            if isinstance(value, str) and len(value) == 0:
                delete_list.append(key)
        for key in delete_list:
            del kwargs[key]

        for field in cls.get_full_fields():
            """Check exists"""
            if cls.is_field_readonly(field):
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
    def get_model_by_snake_case_name(name: str) -> Optional[Type['AvishanModel']]:
        for model in AvishanModel.get_non_abstract_models():
            if model.class_snake_case_name() == name:
                return model
        return None

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
        raise ValueError(AvishanTranslatable(
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
                isinstance(field, models.DateField) or isinstance(field, models.TimeField) and (
                field.auto_now or field.auto_now_add):
            return False
        if isinstance(field, models.ManyToManyField):
            return False

        if field.blank or field.null:
            return False

        return True

    @classmethod
    def cast_field_data(cls, data, field: models.Field):
        """
        Cast data to it's appropriate form
        :param data: entered data
        :param field: target field
        :return: after cast data
        """
        if isinstance(field, (models.CharField, models.TextField)):
            cast_class = str
        elif isinstance(field, (models.IntegerField, models.AutoField)):
            cast_class = int
        elif isinstance(field, models.FloatField):
            cast_class = float
        elif isinstance(field, models.TimeField):
            if not isinstance(data, datetime.time):
                cast_class = datetime.time
            else:
                cast_class = None
        elif isinstance(field, models.DateTimeField):
            if not isinstance(data, datetime.datetime):
                cast_class = datetime.datetime
            else:
                cast_class = None
        elif isinstance(field, models.DateField):
            if not isinstance(data, datetime.date):
                cast_class = datetime.date
            else:
                cast_class = None
        elif isinstance(field, models.BooleanField):
            cast_class = bool
        elif isinstance(field, models.ManyToManyField):
            cast_class = field.related_model
        elif isinstance(field, models.ForeignKey):
            cast_class = field.related_model
        else:
            raise NotImplementedError(AvishanTranslatable(
                EN='cast_field_data not defined cast type',
            ))

        if cast_class is None:
            return data
        if isinstance(cast_class, AvishanModel):
            if not isinstance(data, dict):
                raise ValueError('ForeignKey or ManyToMany relation should contain dict with id')
            output = cast_class.objects.get(id=int(data['id']))
        elif isinstance(cast_class, datetime.datetime):
            if not isinstance(data, dict):
                raise ValueError('Datetime should contain dict')
            output = BchDatetime(data).to_datetime()
        elif isinstance(cast_class, datetime.date):
            if not isinstance(data, dict):
                raise ValueError('Date should contain dict')
            output = BchDatetime(data).to_date()
        else:
            output = cast_class(data)

        return output

    @classmethod
    def __get_object_from_dict(cls, input_dict: dict) -> 'AvishanModel':
        return cls.get(**input_dict)

    # todo 0.2.2: check None amount for choice added fields
    def get_data_from_field(self, field: models.Field, string_format_dates: bool = False):
        from avishan.exceptions import ErrorMessageException
        from avishan_config import AvishanConfig
        if field.choices is not None:
            for k, v in field.choices:
                if k == self.__getattribute__(field.name):
                    return v
            raise ErrorMessageException(AvishanTranslatable(
                EN=f'Incorrect Data entered for field {field.name} in model {self.class_name()}',
                FA=f'اطلاعات نامعتبر برای فیلد {field.name} مدل {self.class_name()}'
            ))
        if string_format_dates:
            if string_format_dates:
                if isinstance(field, models.DateTimeField):
                    if AvishanConfig.USE_JALALI_DATETIME:
                        return BchDatetime(self.__getattribute__(field.name)).to_str('%Y/%m/%d %H:%M:%S')
                    return self.__getattribute__(field.name).strftime("%Y/%m/%d %H:%M:%S")
                if isinstance(field, models.DateField):
                    if AvishanConfig.USE_JALALI_DATETIME:
                        return BchDatetime(self.__getattribute__(field.name)).to_str('%Y/%m/%d')
                    return self.__getattribute__(field.name).strftime("%Y/%m/%d")
                if isinstance(field, models.TimeField):
                    return self.__getattribute__(field.name).strftime("%H:%M:%S")
            return self.__getattribute__(field.name)

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


class BaseUser(AvishanModel):
    """
    Avishan user object. Name changed to "BaseUser" instead of "User" to make this model name available for app models.
    """

    """Only active users can use system. This field checks on every request"""
    is_active = models.BooleanField(default=True, blank=True)

    """
    The first time user attracted with system. This will set on the first models.authentication.BaseUser model creation.
    """
    date_created = models.DateTimeField(auto_now_add=True)

    private_fields = [date_created, 'id']

    def add_to_user_group(self, user_group: 'UserGroup') -> 'UserUserGroup':
        return user_group.add_user_to_user_group(self)

    @classmethod
    def create(cls, is_active: bool = True):
        return super().create(is_active=is_active)

    def __str__(self):
        if hasattr(self, 'user'):
            return str(self.user)
        return super().__str__()
    # todo ye rahi bezarim in betoone username mese adam bargardoone


class UserGroup(AvishanModel):
    """
    Every user most have at least one user group. User group controls it's member's overall activities. Every user have
    an models.authentication.UserUserGroup to manage it's group membership.
    """

    """Unique titles for groups. examples: Customer, User, Driver, Admin, Supervisor"""
    title = models.CharField(max_length=255, unique=True)

    token_valid_seconds = models.BigIntegerField(default=30 * 60, blank=True)

    """Check if this group users can access to their specific space in this ways"""
    authenticate_with_email_password = models.BooleanField(default=False)
    authenticate_with_phone_password = models.BooleanField(default=False)

    private_fields = [token_valid_seconds, 'id', authenticate_with_email_password, authenticate_with_phone_password]

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
    base_user = models.ForeignKey(BaseUser, on_delete=models.CASCADE, related_name='user_user_groups')
    user_group = models.ForeignKey(UserGroup, on_delete=models.CASCADE, related_name='user_user_groups')

    """Date this link created between user and user group"""
    date_created = models.DateTimeField(auto_now_add=True)

    """
    Each token have address to models.authentication.UserUserGroup object. If this fields become false, user cannot use 
    system with this role. "is_active" field on models.authentication.BaseUser will not override on this field. 
    """
    is_active = models.BooleanField(default=True, blank=True)

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

    @classmethod
    def create(cls, user_group: UserGroup, base_user: BaseUser = None):
        if base_user is None:
            base_user = BaseUser.create()
        return super().create(user_group=user_group, base_user=base_user)

    def __str__(self):
        return f'{self.base_user} - {self.user_group}'


class Email(AvishanModel):
    address = models.CharField(max_length=255, unique=True)
    is_verified = models.BooleanField(default=False)

    @staticmethod
    def send_bulk_mail(subject: str, message: str, recipient_list: list, html_message: str = None):
        from avishan_config import AvishanConfig
        from django.core.mail import send_mail
        if html_message is not None:
            send_mail(subject, message, AvishanConfig.EMAIL_SENDER_ADDRESS, recipient_list, html_message)
        else:
            send_mail(subject, message, AvishanConfig.EMAIL_SENDER_ADDRESS, recipient_list)

    def send_mail(self, subject: str, message: str, html_message: str = None):
        self.send_bulk_mail(subject, message, [self.address], html_message)

    def send_verification_code(self):
        # todo calculate time
        email_verification = EmailVerification.create_verification(email=self)
        self.send_mail(
            subject='Cayload Verification Code',
            message=f'Your verification code is: {email_verification.verification_code}'
        )

    def verify(self, code: str):
        if EmailVerification.check_email(self, code):
            self.is_verified = True

    def __str__(self):
        return self.address

    @staticmethod
    def validate_signature(email: str) -> str:
        return email  # todo

    @staticmethod
    def get_or_create_email(email_address: str) -> 'Email':
        try:
            return Email.get(address=email_address)
        except Email.DoesNotExist:
            return Email.create(address=email_address)
        except Exception as e:
            a = 1

    @classmethod
    def get(cls, address: str = None, avishan_to_dict: bool = False, avishan_raise_400: bool = False,
            **kwargs) -> 'Email':
        return super().get(avishan_to_dict, avishan_raise_400, address=cls.validate_signature(address), **kwargs)

    @classmethod
    def create(cls, address: str = None) -> 'Email':
        return super().create(address=cls.validate_signature(address))

    def update(self, address: str = None) -> 'Email':
        return super().update(address=self.validate_signature(address))

    @classmethod
    def filter(cls, avishan_to_dict: bool = False, **kwargs):
        data = {
            'avishan_to_dict': avishan_to_dict, **kwargs
        }
        if 'address' in data.keys():
            data['address'] = cls.validate_signature(kwargs['address'])
        return super().filter(**data)


class EmailVerification(AvishanModel):
    email = models.OneToOneField(Email, on_delete=models.CASCADE, related_name='verification')
    verification_code = models.CharField(max_length=255, blank=True, null=True, default=None)
    verification_date = models.DateTimeField(auto_now_add=True)
    tried_codes = models.TextField(blank=True, default="")

    private_fields = [verification_code, verification_date, tried_codes]

    @staticmethod
    def create_verification(email: Email) -> 'EmailVerification':
        from avishan.exceptions import ErrorMessageException
        from avishan_config import AvishanConfig

        if hasattr(email, 'verification'):
            previous = email.verification
            if BchDatetime() - BchDatetime(previous.verification_date) < AvishanConfig.EMAIL_VERIFICATION_GAP_SECONDS:
                raise ErrorMessageException(AvishanTranslatable(
                    EN='Verification Code sent recently, Please try again later'
                ), status_code=status.HTTP_401_UNAUTHORIZED)
            previous.remove()
        return EmailVerification.create(email=email, verification_code=EmailVerification.create_verification_code())

    @staticmethod
    def check_email(email: Email, code: str) -> bool:
        from avishan.exceptions import ErrorMessageException
        from avishan_config import AvishanConfig
        try:
            item = EmailVerification.get(email=email)
        except EmailVerification.DoesNotExist:
            raise ErrorMessageException(AvishanTranslatable(
                EN=f'Email Verification not found for email {email}'
            ))
        if BchDatetime() - BchDatetime(item.verification_date) > AvishanConfig.EMAIL_VERIFICATION_VALID_SECONDS:
            item.remove()
            raise ErrorMessageException(AvishanTranslatable(
                EN='Code Expired, Request new one'
            ))
        if item.verification_code == code:
            item.remove()
            return True
        if len(item.tried_codes.splitlines()) > AvishanConfig.EMAIL_VERIFICATION_TRIES_COUNT - 1:
            item.remove()
            raise ErrorMessageException(AvishanTranslatable(
                EN=f'Incorrect code repeated {AvishanConfig.EMAIL_VERIFICATION_TRIES_COUNT} times, request new code'
            ))
        item.tried_codes += f"{code}\n"
        item.save()
        raise ErrorMessageException(AvishanTranslatable(
            EN='Incorrect code'
        ))

    @staticmethod
    def create_verification_code() -> str:
        from avishan_config import AvishanConfig
        import random
        return str(random.randint(
            10 ** AvishanConfig.EMAIL_VERIFICATION_CODE_LENGTH,
            10 ** (AvishanConfig.EMAIL_VERIFICATION_CODE_LENGTH + 1) - 1)
        )


class Phone(AvishanModel):
    number = models.CharField(max_length=255, unique=True)
    is_verified = models.BooleanField(default=False)

    @staticmethod
    def send_bulk_sms():
        pass  # todo

    def send_sms(self):
        pass  # todo

    def send_verification_sms(self, code):
        from avishan_config import AvishanConfig
        self.send_template_sms(AvishanConfig.SMS_SIGNIN_TEMPLATE, token=code)

    def send_signup_verification_sms(self, code):
        from avishan_config import AvishanConfig
        self.send_template_sms(AvishanConfig.SMS_SIGNUP_TEMPLATE, token=code)

    def send_template_sms(self, template_name, **kwargs):
        from avishan_config import AvishanConfig
        url = "https://api.kavenegar.com/v1/" + AvishanConfig.KAVENEGAR_API_TOKEN + "/verify/lookup.json"
        querystring = {**{"receptor": self.number, "template": template_name}, **kwargs}
        requests.request("GET", url, data="", headers={}, params=querystring)

    def verify(self, code: str):
        if PhoneVerification.check_phone(self, code):
            self.is_verified = True

    def __str__(self):
        return self.number

    @staticmethod
    def validate_signature(phone: str, country_code: str = "98") -> str:
        from avishan.exceptions import ErrorMessageException
        from .utils import en_numbers
        phone = en_numbers(phone)
        phone = phone.replace(" ", "")
        phone = phone.replace("-", "")

        if phone.startswith("00"):
            if not phone.startswith("00" + country_code):
                raise ErrorMessageException('شماره موبایل', status_code=status.HTTP_417_EXPECTATION_FAILED)
            if phone.startswith("00" + country_code + "09"):
                phone = "00" + country_code + phone[5:]
        elif phone.startswith("+"):
            if not phone.startswith("+" + country_code):
                raise ErrorMessageException('شماره موبایل', status_code=status.HTTP_417_EXPECTATION_FAILED)
            phone = "00" + phone[1:]
            if phone.startswith("00" + country_code + "09"):
                phone = "00" + country_code + phone[5:]
        elif phone.startswith("09"):
            phone = "00" + country_code + phone[1:]

        if len(phone) != 14 or not phone.isdigit():
            raise ErrorMessageException('شماره موبایل', status_code=status.HTTP_417_EXPECTATION_FAILED)

        return phone

    @staticmethod
    def get_or_create_phone(phone_number: str) -> 'Phone':
        try:
            return Phone.get(number=phone_number)
        except Phone.DoesNotExist:
            return Phone.create(number=phone_number)

    @classmethod
    def get(cls, number: str = None, avishan_to_dict: bool = False, avishan_raise_400: bool = False,
            **kwargs) -> 'Phone':
        return super().get(avishan_to_dict, avishan_raise_400, number=cls.validate_signature(number), **kwargs)

    @classmethod
    def create(cls, number: str = None) -> 'Phone':
        return super().create(number=cls.validate_signature(number))

    def update(self, number: str = None) -> 'Phone':
        return super().update(number=self.validate_signature(number))

    @classmethod
    def filter(cls, avishan_to_dict: bool = False, **kwargs):
        data = {
            'avishan_to_dict': avishan_to_dict, **kwargs
        }
        if 'number' in data.keys():
            data['number'] = cls.validate_signature(kwargs['number'])
        return super().filter(**data)


class PhoneVerification(AvishanModel):
    phone = models.OneToOneField(Phone, on_delete=models.CASCADE, related_name='verification')
    verification_code = models.CharField(max_length=255, blank=True, null=True, default=None)
    verification_date = models.DateTimeField(auto_now_add=True)
    tried_codes = models.TextField(blank=True, default="")

    private_fields = [verification_code, verification_date, tried_codes]

    @staticmethod
    def create_verification(phone: Phone) -> 'PhoneVerification':
        from avishan.exceptions import ErrorMessageException
        from avishan_config import AvishanConfig

        if hasattr(phone, 'verification'):
            previous = phone.verification
            if BchDatetime() - BchDatetime(previous.verification_date) < AvishanConfig.PHONE_VERIFICATION_GAP_SECONDS:
                raise ErrorMessageException(AvishanTranslatable(
                    EN='Verification Code sent recently, Please try again later'
                ), status_code=status.HTTP_401_UNAUTHORIZED)
            previous.remove()
        return PhoneVerification.create(phone=phone, verification_code=PhoneVerification.create_verification_code())

    @staticmethod
    def check_phone(phone: Phone, code: str) -> bool:
        from avishan.exceptions import ErrorMessageException
        from avishan_config import AvishanConfig
        try:
            item = PhoneVerification.get(phone=phone)
        except PhoneVerification.DoesNotExist:
            raise ErrorMessageException(AvishanTranslatable(
                EN=f'Phone Verification not found for phone {phone}'
            ))
        if BchDatetime() - BchDatetime(item.verification_date) > AvishanConfig.PHONE_VERIFICATION_VALID_SECONDS:
            item.remove()
            raise ErrorMessageException(AvishanTranslatable(
                EN='Code Expired, Request new one'
            ))
        if item.verification_code == code:
            item.remove()
            return True
        if len(item.tried_codes.splitlines()) > AvishanConfig.PHONE_VERIFICATION_TRIES_COUNT - 1:
            item.remove()
            raise ErrorMessageException(AvishanTranslatable(
                EN=f'Incorrect Code repeated {AvishanConfig.PHONE_VERIFICATION_TRIES_COUNT} times, request new code'
            ))
        item.tried_codes += f"{code}\n"
        item.save()
        raise ErrorMessageException(AvishanTranslatable(
            EN='Incorrect Code'
        ))

    @staticmethod
    def create_verification_code() -> str:
        from avishan_config import AvishanConfig
        import random
        return str(random.randint(
            10 ** AvishanConfig.PHONE_VERIFICATION_CODE_LENGTH,
            10 ** (AvishanConfig.PHONE_VERIFICATION_CODE_LENGTH + 1) - 1)
        )


class AuthenticationType(AvishanModel):
    user_user_group = models.OneToOneField(UserUserGroup, on_delete=models.CASCADE)
    last_used = models.DateTimeField(default=None, blank=True, null=True)
    last_login = models.DateTimeField(default=None, blank=True, null=True)
    last_logout = models.DateTimeField(default=None, blank=True, null=True)

    class Meta:
        abstract = True

    def _logout(self):
        self.last_logout = BchDatetime().to_datetime()
        self.save()
        current_request['authentication_object'] = None
        current_request['add_token'] = False

    def _login(self):
        from avishan.utils import populate_current_request

        self.last_login = BchDatetime().to_datetime()
        self.last_logout = None
        self.save()
        populate_current_request(self)


class KeyValueAuthentication(AuthenticationType):
    hashed_password = models.CharField(max_length=255, blank=True, null=True, default=None)

    @classmethod
    def key_field(cls) -> models.ForeignKey:
        raise NotImplementedError()

    # todo 0.2.2: bara verification che bokonim?

    class Meta:
        abstract = True

    @staticmethod
    def _hash_password(password: str) -> str:
        """
        Hash entered password
        :param password:
        :return: hashed password in string
        """
        import bcrypt
        return bcrypt.hashpw(password.encode('utf8'), bcrypt.gensalt()).decode('utf8')

    @staticmethod
    def _check_password(password: str, hashed_password: str) -> bool:
        """
        compares password with hashed instance.
        :param password:
        :param hashed_password:
        :return: True if match
        """
        import bcrypt
        return bcrypt.checkpw(password.encode('utf8'), hashed_password.encode('utf8'))

    @classmethod
    def register(cls, user_user_group: UserUserGroup, key: str, password: Optional[str] = None) -> \
            Union['EmailPasswordAuthenticate', 'PhonePasswordAuthenticate']:
        """
        Registration process for key-value authentications
        :param user_user_group:
        :param key: email, phone, ...
        :param password:
        :param kwargs:
        :return:
        """
        from avishan.exceptions import AuthException

        try:
            key_item = cls.key_field().related_model.get(key)
        except cls.key_field().related_model.DoesNotExist:
            key_item = cls.key_field().related_model.create(key)
        try:
            cls.objects.get(**{cls.key_field().name: key_item, 'user_user_group': user_user_group})
            raise AuthException(AuthException.DUPLICATE_AUTHENTICATION_IDENTIFIER)
        except cls.DoesNotExist:
            # todo 0.2.3: auto reach to related
            if hasattr(user_user_group, cls.key_field().name + 'passwordauthenticate'):
                raise AuthException(AuthException.DUPLICATE_AUTHENTICATION_TYPE)
        data = {
            'user_user_group': user_user_group,
            cls.key_field().name: key_item,
        }
        if password is not None:
            data['hashed_password'] = cls._hash_password(password)

        return cls.objects.create(**data)

    def add_password(self, password: str) -> bool:
        if self.hashed_password is None:
            self.hashed_password = self._hash_password(password)
            self.save()
            return True
        return False

    @classmethod
    def login(cls, key: str, password: str, user_group: UserGroup = None) -> \
            Union['EmailPasswordAuthenticate', 'PhonePasswordAuthenticate']:
        from avishan.exceptions import AuthException

        try:
            found_object = cls.objects.get(
                **{
                    cls.key_field().name: cls.key_field().related_model.get(key),
                    "user_user_group__user_group": user_group
                }
            )
        except (cls.DoesNotExist, cls.key_field().related_model.DoesNotExist):
            raise AuthException(AuthException.ACCOUNT_NOT_FOUND)
        if not cls._check_password(password, found_object.hashed_password):
            # todo 0.2.3: count incorrect enters with time, ban after some time
            raise AuthException(AuthException.INCORRECT_PASSWORD)

        found_object._login()
        return found_object

    @classmethod
    def find(cls, key: str, password: str = None, user_group: UserGroup = None) -> \
            List[Union['EmailPasswordAuthenticate', 'PhonePasswordAuthenticate']]:
        key = cls.key_field().related_model.validate_signature(key)
        kwargs = {}
        if user_group:
            kwargs['user_user_group__user_group'] = user_group
        try:
            kwargs[cls.key_field().name] = cls.key_field().related_model.get(key)
        except cls.key_field().related_model.DoesNotExist:
            return []

        founds = cls.objects.filter(**kwargs)
        if password:
            for found in founds:
                if found._check_password(password, found.hashed_password):
                    return [found]
            return []
        return founds


class EmailPasswordAuthenticate(KeyValueAuthentication):
    email = models.ForeignKey(Email, on_delete=models.CASCADE, related_name='password_authenticates')
    django_admin_list_display = [email, 'user_user_group', 'last_used', 'last_login', 'last_logout']

    @classmethod
    def key_field(cls) -> Union[models.ForeignKey, models.Field]:
        return cls.get_field('email')


class PhonePasswordAuthenticate(KeyValueAuthentication):
    phone = models.ForeignKey(Phone, on_delete=models.CASCADE, related_name='password_authenticates')

    django_admin_list_display = ['user_user_group', phone]

    @classmethod
    def key_field(self) -> Union[models.ForeignKey, models.Field]:
        return self.get_field('phone')


class OTPAuthentication(AuthenticationType):
    code = models.CharField(max_length=255, blank=True, null=True)
    date_sent = models.DateTimeField(null=True, blank=True, default=None)
    tried_codes = models.TextField(blank=True, default="")

    class Meta:
        abstract = True

    @classmethod
    def key_field(cls) -> models.ForeignKey:
        raise NotImplementedError()

    @staticmethod
    def create_otp_code() -> str:
        from avishan_config import AvishanConfig
        return str(random.randint(10 ** (AvishanConfig.OTP_CODE_LENGTH - 1), 10 ** AvishanConfig.OTP_CODE_LENGTH - 1))

    def check_verification_code(self, entered_code: str) -> bool:
        from avishan.exceptions import ErrorMessageException
        from avishan_config import AvishanConfig
        if self.code is None:
            raise ErrorMessageException(AvishanTranslatable(
                EN='Code not found for this account',
                FA='برای این حساب کدی پیدا نشد'
            ))
        if (BchDatetime() - BchDatetime(self.date_sent)).total_seconds() > AvishanConfig.PHONE_OTP_CODE_VALID_SECONDS:
            self.code = None
            self.save()
            raise ErrorMessageException(AvishanTranslatable(
                EN='Code Expired',
                FA='کد منقضی شده است'
            ))

        if self.code != entered_code:
            self.tried_codes += f"{entered_code} - {BchDatetime().to_datetime()}\n"
            self.save()
            return False

        self.code = None
        self.tried_codes = ""
        self.save()
        return True

    @classmethod
    def create_new(cls, user_user_group: UserUserGroup, key: str) -> 'PhoneOTPAuthenticate':
        from avishan.exceptions import AuthException
        try:
            key_item = cls.key_field().related_model.get(key)
        except cls.key_field().related_model.DoesNotExist:
            key_item = cls.key_field().related_model.create(key)
        try:
            cls.objects.get(**{cls.key_field().name: key_item, 'user_user_group': user_user_group})
            raise AuthException(AuthException.DUPLICATE_AUTHENTICATION_IDENTIFIER)
        except cls.DoesNotExist:
            if hasattr(user_user_group, cls.key_field().name + 'otpauthenticate'):
                raise AuthException(AuthException.DUPLICATE_AUTHENTICATION_TYPE)
        return cls.objects.create(**{
            'user_user_group': user_user_group,
            cls.key_field().name: key_item
        })

    def verify_account(self) -> Union['OTPAuthentication', 'PhoneOTPAuthenticate']:
        self.send_otp_code()

        return self

    @classmethod
    def check_authentication(cls, key: str, entered_code: str, user_group: UserGroup) -> Tuple[
        'PhoneOTPAuthenticate', bool]:
        from avishan.exceptions import AuthException
        try:
            item = cls.find(key, user_group)[0]
        except IndexError:
            raise AuthException(AuthException.ACCOUNT_NOT_FOUND)

        if not item.check_verification_code(entered_code):
            raise AuthException(AuthException.INCORRECT_PASSWORD)

        if item.last_login is None:
            created = True
            item.user_user_group.base_user.is_active = True
            item.user_user_group.base_user.save()
        else:
            created = False

        item._login()
        return item, created

    def send_otp_code(self):
        raise NotImplementedError()

    @classmethod
    def find(cls, key: str, user_group: UserGroup = None) -> List['PhoneOTPAuthenticate']:
        key = cls.key_field().related_model.validate_signature(key)
        kwargs = {}
        if user_group:
            kwargs['user_user_group__user_group'] = user_group
        try:
            kwargs[cls.key_field().name] = cls.key_field().related_model.get(key)
        except cls.key_field().related_model.DoesNotExist:
            return []

        return cls.objects.filter(**kwargs)


class PhoneOTPAuthenticate(OTPAuthentication):
    phone = models.ForeignKey(Phone, on_delete=models.CASCADE, related_name='otp_authenticates')

    @classmethod
    def key_field(cls) -> Union[models.Field, models.ForeignKey]:
        return cls.get_field('phone')

    def send_otp_code(self):
        self.code = self.create_otp_code()
        self.date_sent = BchDatetime().to_datetime()
        self.phone.send_verification_sms(self.code)
        self.save()


class Image(AvishanModel):
    file = models.ImageField(blank=True, null=True)
    base_user = models.ForeignKey(BaseUser, on_delete=models.SET_NULL, null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.url

    @staticmethod
    def image_from_url(url: str) -> 'Image':
        """
        :param url: like "core/init_files/blue-car.png"
        """
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
            'url': self.file.url
        }

    @classmethod
    def image_from_multipart_form_data_request(cls, name: str = 'file') -> 'Image':
        from avishan.exceptions import ErrorMessageException
        media = current_request['request'].FILES.get(name)
        if media is None:
            raise ErrorMessageException(AvishanTranslatable(
                EN='File not found',
                FA='فایل ارسال نشده است'
            ))

        created = Image.create(
            base_user=current_request['base_user']
        )
        created.file.save("uploaded_images/" + media.name, media, save=True)
        created.save()

        return created


class File(AvishanModel):
    file = models.FileField(blank=True, null=True)
    base_user = models.ForeignKey(BaseUser, on_delete=models.SET_NULL, null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)

    def to_dict(self, exclude_list: List[Union[models.Field, str]] = ()) -> dict:
        return {
            'id': self.id,
            'url': self.file.url
        }


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
    request_headers = models.TextField(null=True, blank=True)
    response_data = models.TextField(null=True, blank=True)
    start_time = models.DateTimeField(blank=True, null=True)
    end_time = models.DateTimeField(blank=True, null=True)
    total_execution_milliseconds = models.BigIntegerField(null=True, blank=True)
    view_execution_milliseconds = models.BigIntegerField(null=True, blank=True)
    authentication_type_class_title = models.CharField(max_length=255, blank=True, null=True)
    authentication_type_object_id = models.IntegerField(blank=True, null=True)

    django_admin_list_display = [view_name, method, status_code, user_user_group, start_time,
                                 total_execution_milliseconds, url]

    def __str__(self):
        return self.view_name

    def create_exec_infos(self, data: list):
        dates = {}
        for part in data:
            dates[part['title']] = part['now']
        for part in data:
            if part['title'] == 'begin':
                continue
            RequestTrackExecInfo.create(
                request_track=self,
                title=part['title'],
                start_time=dates[part['from_title']],
                end_time=part['now'],
                milliseconds=(part['now'] - dates[part['from_title']]).total_seconds() * 1000
            )


class RequestTrackExecInfo(AvishanModel):
    request_track = models.ForeignKey(RequestTrack, on_delete=models.CASCADE, related_name='exec_infos')
    title = models.CharField(max_length=255)
    start_time = models.DateTimeField(blank=True, null=True)
    end_time = models.DateTimeField(blank=True, null=True)
    milliseconds = models.FloatField(default=None, null=True, blank=True)

    django_admin_list_display = (request_track, title, start_time, milliseconds)
    django_admin_list_filter = (request_track, title)
    django_admin_list_max_show_all = 500
    django_admin_search_fields = (title,)

    @classmethod
    def create_dict(cls, title: str, from_title: str = 'begin'):
        current_request['request_track_exec'].append({
            'title': title,
            'from_title': from_title,
            'now': datetime.datetime.now()
        })

    def __str__(self):
        return self.title


class RequestTrackMessage(AvishanModel):
    request_track = models.ForeignKey(RequestTrack, on_delete=models.CASCADE, related_name='messages')
    type = models.CharField(max_length=255)
    title = models.TextField(null=True, blank=True)
    body = models.TextField(null=True, blank=True)
    code = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.title


class RequestTrackException(AvishanModel):
    request_track = models.OneToOneField(RequestTrack, on_delete=models.CASCADE, related_name='exception')
    class_title = models.CharField(max_length=255, null=True, blank=True)
    args = models.TextField(null=True, blank=True)
    traceback = models.TextField(null=True, blank=True)

    django_admin_list_display = [request_track, class_title, args]


class TranslatableChar(AvishanModel):
    en = models.CharField(max_length=255, blank=True, null=True, default=None)
    fa = models.CharField(max_length=255, blank=True, null=True, default=None)

    @classmethod
    def create(cls, en: str = None, fa: str = None, auto: str = None):
        from avishan.exceptions import ErrorMessageException

        kwargs = {}
        if auto:
            if current_request['lang'] is None:
                raise ErrorMessageException(AvishanTranslatable(
                    EN='language not set',
                    FA='زبان تنظیم نشده است'
                ))
            kwargs[current_request['lang']] = auto
        if en is not None:
            en = str(en)
            if len(en) == 0:
                en = None
        if fa is not None:
            fa = str(fa)
            if len(fa) == 0:
                fa = None
        return super().create(en=en, fa=fa)

    def __str__(self):
        return AvishanTranslatable(EN=self.en, FA=self.fa)
