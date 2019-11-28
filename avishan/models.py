from typing import List, Type, Tuple, Union

from django.db.models import NOT_PROVIDED

from avishan import current_request
from avishan.exceptions import ErrorMessageException
from avishan.misc import translatable

import datetime
from typing import Optional

from avishan.misc.bch_datetime import BchDatetime
from django.db import models


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
                    if kwargs[field.name] == {'id': 0}:
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

    def add_to_user_group(self, user_group: 'UserGroup') -> 'UserUserGroup':
        return user_group.add_user_to_user_group(self)


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


class AuthenticationType(AvishanModel):
    user_user_group = models.OneToOneField(UserUserGroup, on_delete=models.CASCADE)
    last_used = models.DateTimeField(default=None, blank=True, null=True)
    last_login = models.DateTimeField(default=None, blank=True, null=True)
    last_logout = models.DateTimeField(default=None, blank=True, null=True)

    class Meta:
        abstract = True

    @staticmethod
    def register(user_user_group: UserUserGroup, **kwargs):
        """
        Factory method which creates object of an authorization type.
        :param user_user_group: target user_user_group object
        :param kwargs: email, password, phone, code, etc.
        """
        raise NotImplementedError()

    @staticmethod
    def login(**kwargs):
        """
        Login with entered data. Can just pass data to do_password_login_actions method
        :param kwargs: entered credential like username, email, password and etc.
        :return: return true if login accepted
        """
        raise NotImplementedError()

    def logout(self):
        self.last_logout = BchDatetime().to_datetime()
        self.save()
        from avishan import current_request
        current_request['authentication_object'] = None
        current_request['add_token'] = False

    @classmethod
    def _do_identifier_password_login(cls, identifier_name: str, identifier_value: str, value_name: str,
                                      value_value: str) -> 'AuthenticationType':
        """
        Doing login action in key-value aspect
        :param identifier_name: identifier name: username, email
        :param identifier_value: identifier value: afshari9978, afshari9978@gmail.com
        :param value_name: checking name: password, code, passphrase
        :param value_value: checking value (unhashed): 123465
        """
        from avishan.exceptions import AuthException
        from avishan.utils import populate_current_request

        try:
            found_object = cls.objects.get(**{identifier_name: identifier_value})
        except cls.DoesNotExist:
            raise AuthException(AuthException.ACCOUNT_NOT_FOUND)
        if not cls._check_password(value_value, found_object.__getattribute__(value_name)):
            # todo 0.2.3: count incorrect enters with time, ban after some time
            raise AuthException(AuthException.INCORRECT_PASSWORD)

        found_object.last_login = BchDatetime().to_datetime()
        found_object.last_logout = None
        found_object.save()

        populate_current_request(found_object)

        return found_object

    @classmethod
    def _do_identifier_password_register(cls, user_user_group: UserUserGroup, identifier_name: str,
                                         identifier_value: str, password_name: str,
                                         password_value: str) -> 'AuthenticationType':
        """
        Register identifier-password authentication type for user. If there be errors, will raise straight.
        :param user_user_group:
        :param identifier_name: examples: 'email', 'phone', 'username'
        :param identifier_value: afshari9978@gmail.com
        :param password_name:
        :param password_value:
        :return:
        """
        from avishan.exceptions import AuthException
        try:
            cls.objects.get(**{identifier_name: identifier_value})
            raise AuthException(AuthException.DUPLICATE_AUTHENTICATION_IDENTIFIER)
        except cls.DoesNotExist:
            if cls.class_name() == 'EmailPasswordAuthenticate':
                related_name = 'emailpasswordauthenticate'
            else:
                related_name = 'phonepasswordauthenticate'
            # todo 0.2.3: auto reach to related
            if hasattr(user_user_group, related_name):
                raise AuthException(AuthException.DUPLICATE_AUTHENTICATION_TYPE)
        created = cls.objects.create(**{
            'user_user_group': user_user_group,
            identifier_name: identifier_value,
            password_name: AuthenticationType._hash_password(password_value)
        })

        return created  # todo 0.2.2: put validator on identifier/password

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
    def identifier_field(cls):
        raise NotImplementedError()

    @classmethod
    def password_field(cls):
        raise NotImplementedError()


class EmailPasswordAuthenticate(AuthenticationType):
    email = models.CharField(max_length=255, unique=True)
    password = models.CharField(max_length=255, blank=True, null=True, default=None)

    @staticmethod
    def register(user_user_group: UserUserGroup, email: str, password: str, **kwargs) -> 'EmailPasswordAuthenticate':
        return EmailPasswordAuthenticate._do_identifier_password_register(user_user_group, 'email', email, 'password',
                                                                          password)

    @staticmethod
    def login(email: str, password: str) -> 'EmailPasswordAuthenticate':
        return EmailPasswordAuthenticate._do_identifier_password_login('email', email, 'password', password)

    @classmethod
    def admin_fields(cls):
        return [cls.get_field('email'), cls.get_field('password')]


class PhonePasswordAuthenticate(AuthenticationType):
    phone = models.CharField(max_length=255, unique=True)
    password = models.CharField(max_length=255, blank=True, null=True, default=None)

    @staticmethod
    def register(user_user_group: UserUserGroup, phone: str, password: str) -> 'PhonePasswordAuthenticate':
        if phone.startswith("09"):
            phone = "0098" + phone[1:]
        elif phone.startswith("9"):
            phone = "0098" + phone
        return PhonePasswordAuthenticate._do_identifier_password_register(user_user_group, 'phone', phone, 'password',
                                                                          password)

    @staticmethod
    def login(phone: str, password: str) -> 'PhonePasswordAuthenticate':
        if phone.startswith("09"):
            phone = "0098" + phone[1:]
        elif phone.startswith("9"):
            phone = "0098" + phone
        return PhonePasswordAuthenticate._do_identifier_password_login('phone', phone, 'password', password)

    @classmethod
    def admin_fields(cls):
        return [cls.get_field('phone'), cls.get_field('password')]

    @classmethod
    def admin_fields_verbose_name(cls):
        return ['شماره همراه', 'رمز عبور']

    @classmethod
    def identifier_field(cls):
        return cls.get_field('phone')

    @classmethod
    def password_field(cls):
        return cls.get_field('password')


class Image(AvishanModel):
    file = models.ImageField(blank=True, null=True)
    base_user = models.ForeignKey(BaseUser, on_delete=models.SET_NULL, null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)


class Video(AvishanModel):
    pass  # todo 0.2.3


class File(AvishanModel):
    file = models.FileField(blank=True, null=True)
    base_user = models.ForeignKey(BaseUser, on_delete=models.SET_NULL, null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)


class ExceptionRecord(AvishanModel):
    class_title = models.CharField(max_length=255)
    user_user_group = models.ForeignKey(UserUserGroup, on_delete=models.SET_NULL, null=True, blank=True)
    status_code = models.IntegerField(blank=True, null=True)
    request_url = models.TextField(blank=True, null=True)
    request_method = models.CharField(max_length=255)
    request_data = models.TextField(blank=True, null=True)
    request_headers = models.TextField(blank=True, null=True)
    response = models.TextField(blank=True, null=True)
    traceback = models.TextField(blank=True, null=True)
    exception_args = models.TextField(blank=True, null=True)
    checked = models.BooleanField(default=False)
    errors = models.TextField(blank=True, null=True)
    warnings = models.TextField(blank=True, null=True)
    is_api = models.BooleanField(default=None, null=True, blank=True)
