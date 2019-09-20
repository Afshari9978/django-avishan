import re
from typing import List, Optional, Type, Tuple

from django.db import models

# todo: encrypted fields: https://django-fernet-fields.readthedocs.io/en/latest/
from django.db.models import QuerySet
from django.db.models.fields import Field, NOT_PROVIDED

from .utils.bch_datetime import BchDatetime


# todo: check access rules in crud
# todo: create a helping class to move many of functions there
class AvishanModel(models.Model):
    date_created = models.DateTimeField(auto_now_add=True)

    compact_fields = []
    private_fields = []
    added_properties = []
    # django admin
    date_hierarchy = None
    list_display = None
    list_filter = []
    list_max_show_all = 300
    list_per_page = 100
    raw_id_fields = []
    readonly_fields = ['date_created']
    search_fields = []

    class ObjectAction:
        GET = 'GET'
        CREATE = 'CREATE'
        UPDATE = 'UPDATE'

    # todo: auto add added properties
    # todo: have to_dict property for each method
    # todo: have private methods for main objects crud start with _
    # todo: on update, create cannot change pk
    class Meta:
        abstract = True

    @classmethod
    def get_fields(cls) -> List[Field]:
        return cls._meta.fields

    @classmethod
    def get_full_fields(cls) -> List[Field]:
        return cls.get_fields() + cls._meta.many_to_many

    @staticmethod
    def is_field_required(field: Field) -> bool:
        if field.name == 'id' or field.default != NOT_PROVIDED or \
                (isinstance(field, models.DateField) or isinstance(field, models.TimeField) and (
                        field.auto_now or field.auto_now_add)):
            return False
        if isinstance(field, models.ManyToManyField):
            return False

        if field.blank or field.null:
            return False

        # todo: is it true?
        return True

    @staticmethod
    def is_field_readonly(field: Field) -> bool:
        if (isinstance(field, models.DateField) or isinstance(field, models.DateTimeField) or
            isinstance(field, models.TimeField)) and (field.auto_now or field.auto_now_add):
            return True
        return False

    @classmethod
    def is_field_identifier_for_model(cls, field: Field, on_create: bool = False) -> bool:
        if on_create and isinstance(field, models.OneToOneField):
            return False
        if on_create and not field.primary_key:
            return False
        return field.primary_key or field.unique

    @classmethod
    def get_readonly_fields(cls) -> list:
        return [field for field in cls.get_fields() if cls.is_field_readonly(field)]

    def __str__(self):
        for field in self.get_fields():
            if isinstance(field, models.CharField):
                return self.__getattribute__(field.name)
        return super().__str__()
        # todo return first field str

    @classmethod
    def get(cls, avishan_raise_400: bool = False,
            avishan_raise_exception: bool = False,
            object_trace: str = "", **kwargs) -> \
            Optional['AvishanModel']:
        # todo oon halati k query mizanim ba __ ha ham bayad vojood dashte bashe
        """
        [X] if not found return None
        [X] if bch datetime sent, convert to datetime
        """
        # todo: remove non identifier attributes to prevent multi level GET

        try:
            return cls.__get(**kwargs)
        except cls.DoesNotExist as e:
            if avishan_raise_400:
                from .exceptions import ErrorMessageException

                raise ErrorMessageException("Chosen " + cls.__name__ + " doesnt exist")  # todo: esme farsi bara model
            if avishan_raise_exception:
                from .utils.data_functions import save_traceback
                save_traceback()
                raise e
            return None

    @classmethod
    def filter(cls, avishan_to_dict: bool = False, **kwargs) -> QuerySet(
        'AvishanModel'):
        """
        [X] if empty kwargs return all
        """
        if avishan_to_dict:
            return [item.to_dict(compact=True) for item in
                    cls.filter(avishan_to_dict=False, **kwargs)]

        if len(kwargs.items()) > 0:
            return cls.objects.filter(**kwargs)
        else:
            return cls.objects.all()

    @classmethod
    def all(cls, avishan_to_dict: bool = False) -> QuerySet('AvishanModel'):
        return cls.filter(avishan_to_dict)

    @classmethod
    def create(cls, avishan_object_trace: str = "",
               avishan_prevent_clean: bool = False,
               **kwargs) -> 'AvishanModel':
        from avishan_wrapper import current_request
        """
        [O] if value error, raise true exception. translate value error
        [O] control field choices
        """

        if not avishan_prevent_clean:
            create_kwargs, after_create_kwargs = cls.__clean_input_data_for_model(kwargs, avishan_object_trace
                                                                                  )
        else:
            create_kwargs = kwargs
            after_create_kwargs = {}

        created = cls.__create(**create_kwargs)

        if after_create_kwargs:
            for key, value in after_create_kwargs.items():
                for item in value:
                    created.__getattribute__(key).add(item)
        created.save()
        return created

    def update(self, avishan_object_trace: str = "", avishan_prevent_clean: bool = False, **kwargs) -> 'AvishanModel':
        if not avishan_prevent_clean:
            in_time_kwargs, many_to_many_kwargs = self.__class__.__clean_input_data_for_model(kwargs,
                                                                                              avishan_object_trace)
        else:
            in_time_kwargs = kwargs
            many_to_many_kwargs = {}
        # todo: remove identifier attributes to prevent update on them
        # todo: check for change. if not changed, dont update
        for key, value in in_time_kwargs.items():
            # todo check values
            self.__setattr__(key, value)

        for key, value in many_to_many_kwargs.items():
            self.__getattribute__(key).clear()
            for item in value:
                self.__getattribute__(key).add(item)
        self.save()
        return self

    def remove(self) -> dict:
        # todo check access
        temp = self.to_dict()
        self.delete()
        return temp

    @classmethod
    def get_required_fields(cls) -> List[Field]:
        return [field for field in cls.get_fields() if cls.is_field_required(field)]

    @classmethod
    def define_object_action(cls, input_dict: dict):

        create_flag = get_flag = False
        for field in cls.get_full_fields():
            if cls.is_field_identifier_for_model(field) and field.name in input_dict.keys():
                get_flag = True

            elif field.name in input_dict.keys():
                create_flag = True

        if create_flag:
            if get_flag:
                return cls.ObjectAction.UPDATE
            return cls.ObjectAction.CREATE
        return cls.ObjectAction.GET

    @classmethod
    def __clean_input_data_for_model(cls, input_dict: dict, previous_object_trace: str) -> Tuple[
        dict, dict]:
        from django.db.models import DateField, DateTimeField, TimeField, OneToOneField, ForeignKey, ManyToManyField
        from .exceptions import ErrorMessageException

        object_trace = previous_object_trace + cls.class_snake_case_name()
        create_kwargs = {}
        after_create_kwargs = {}
        for field in cls.get_full_fields():
            if cls.is_field_identifier_for_model(field, on_create=True) \
                    or (isinstance(field, (DateField, TimeField)) and (field.auto_now or field.auto_now_add)):
                continue
            elif cls.is_field_required(field) and field.name not in input_dict.keys():
                raise ErrorMessageException(
                    f'Field {field.name} not found in object {cls.class_name()}, and it\'s required.'
                )

            elif field.name not in input_dict.keys():
                continue

            elif isinstance(field, (OneToOneField, ForeignKey)):
                if isinstance(input_dict[field.name], models.Model):
                    create_kwargs[field.name] = input_dict[field.name]
                else:
                    length = len(object_trace)
                    object_trace += "->" + field.name + ":"
                    create_kwargs[field.name] = field.related_model.__get_object_from_dict(input_dict[field.name],
                                                                                           object_trace)
                    object_trace = object_trace[:length]

            elif isinstance(field, ManyToManyField):

                after_create_kwargs[field.name] = []
                length = len(object_trace)
                object_trace += "->" + field.name + ":"
                for input_item in input_dict[field.name]:
                    if isinstance(input_item, models.Model):
                        item_object = input_item
                    else:
                        item_object = field.related_model.__get_object_from_dict(input_item, object_trace)
                    after_create_kwargs[field.name].append(
                        item_object
                    )
                object_trace = object_trace[:length]

            else:
                create_kwargs[field.name] = input_dict[field.name]
                if isinstance(input_dict[field.name], BchDatetime):
                    if isinstance(field, DateTimeField):
                        create_kwargs[field.name] = input_dict[field.name].to_datetime()
                    elif isinstance(field, DateField):
                        create_kwargs[field.name] = input_dict[field.name].to_date()
                    elif isinstance(field, TimeField):
                        create_kwargs[field.name] = input_dict[field.name].to_time()
                    else:
                        raise ErrorMessageException('خطای نامشخص در سیستم زمانی')
        return create_kwargs, after_create_kwargs

    @classmethod
    def __get_object_from_dict(cls, input_dict: dict, previous_object_trace: str, reach_to_object: bool = True) -> \
            'AvishanModel':
        from .exceptions import AuthException, ErrorMessageException
        from avishan_wrapper import current_request
        from .utils import status
        object_trace = previous_object_trace + cls.class_snake_case_name()

        defined_action = cls.define_object_action(input_dict)

        if defined_action == cls.ObjectAction.GET:
            # todo check access age raise kard chi aghaye mir salim?
            try:
                return cls.get(avishan_raise_exception=True,
                               object_trace=object_trace, **input_dict)
            except cls.DoesNotExist:
                current_request['response']['object_trace'] = object_trace
                current_request['response']['available_data'] = input_dict
                from .utils.data_functions import save_traceback
                save_traceback()
                raise ErrorMessageException('Object not found with available data.',
                                            status_code=status.HTTP_406_NOT_ACCEPTABLE)

        elif defined_action == cls.ObjectAction.CREATE:
            return cls.create(**input_dict)

        elif defined_action == cls.ObjectAction.UPDATE:
            try:
                found = cls.get(avishan_raise_exception=True, object_trace=object_trace, **input_dict)
            except cls.DoesNotExist:
                current_request['response']['object_trace'] = object_trace
                current_request['response']['available_data'] = input_dict
                from .utils.data_functions import save_traceback
                save_traceback()
                raise ErrorMessageException('Object not found with available data.',
                                            status_code=status.HTTP_406_NOT_ACCEPTABLE)
            return found.update(avishan_object_trace=object_trace,
                                **input_dict)
        # raise FuckException todo create fuck exception

    def to_dict(self: 'AvishanModel', compact: bool = False, except_list: list = None,
                visible_list: list = None) -> dict:
        from datetime import time
        from .utils.model_functions import filter_added_properties, filter_private_fields, filter_compact_fields, \
            filter_except_list
        # todo objectifire kamel
        # todo __dict__ ?

        dicted = {}

        if not visible_list:
            visible_list = []
        if not except_list:
            except_list = []

        field_names = []
        for field in self.get_full_fields():
            field_names.append(field.name)

        field_names = filter_added_properties(field_names, self)
        field_names = filter_private_fields(field_names, self, visible_list)
        if compact:
            field_names = filter_compact_fields(field_names, self)
        field_names = filter_except_list(field_names, except_list)

        for field in self.get_full_fields():
            if field.name not in field_names:
                continue

            value = self.__getattribute__(field.name)
            if value is None:
                dicted[field.name] = {}
            elif isinstance(field, (models.DateField)):
                dicted[field.name] = BchDatetime(value).to_dict(full=True)
            elif isinstance(field, (models.OneToOneField, models.ForeignKey)):
                dicted[field.name] = value.to_dict()
            elif isinstance(field, models.ManyToManyField):
                dicted[field.name] = []
                for item in value.all():
                    dicted[field.name].append(item.to_dict())
            elif isinstance(value, time):
                dicted[field.name] = {
                    'hour': value.hour, 'minute': value.minute, 'second': value.second, 'microsecond': value.microsecond
                }
            else:
                dicted[field.name] = value

        for field_name in filter_added_properties(field_names, self):
            if field_name in field_names and field_name not in dicted.keys():
                dicted[field_name] = self.__getattribute__(field_name)

        return dicted

    @classmethod
    def class_snake_case_name(cls) -> str:
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', cls.class_name())
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    @classmethod
    def class_name(cls) -> str:
        return cls.__name__

    @classmethod
    def class_plural_snake_case_name(cls) -> str:
        return cls.class_snake_case_name() + "s"

    @classmethod
    def app_name(cls) -> str:
        return cls._meta.app_label

    @classmethod
    def update_or_create_object(cls, fixed_kwargs: dict, new_additional_kwargs: dict) -> Tuple[
        Type['AvishanModel'], bool]:
        try:
            found = cls.get(avishan_raise_exception=True, **fixed_kwargs)
            return found.update(**{**fixed_kwargs, **new_additional_kwargs}), False
        except cls.DoesNotExist:
            return cls.create(**{**fixed_kwargs, **new_additional_kwargs}), True

    @classmethod
    def get_target_type_from_field(cls, field: Field) -> type:
        if isinstance(field, (models.CharField, models.TextField)):
            return str
        if isinstance(field, (models.IntegerField, models.AutoField)):
            return int
        if isinstance(field, models.FloatField):
            return float
        if isinstance(field, models.TimeField):
            import datetime
            return datetime.time
        if isinstance(field, models.DateField):
            import datetime
            return datetime.date
        if isinstance(field, models.DateTimeField):
            import datetime
            return datetime.datetime
        if isinstance(field, models.BooleanField):
            return bool
        if isinstance(field, models.FileField):
            return File  # todo doros she
        if isinstance(field, models.ForeignKey):
            return field.related_model

        raise NotImplementedError(
            f'get_target_type_from_field function with cls: {cls.class_name()} and field {field.name}')

    @classmethod
    def __get(cls, **kwargs):
        return cls.objects.get(**kwargs)

    @classmethod
    def __create(cls, **kwargs) -> 'AvishanModel':
        return cls.objects.create(**kwargs)


class Image(AvishanModel):
    file = models.ImageField(blank=True)
    private_fields = ('date_created',)
    list_display = ('__str__', 'date_created')

    def __str__(self):
        return self.file.name

    def to_dict(self, **kwargs) -> dict:
        temp = {}
        temp['url'] = self.file.url
        temp['id'] = self.id
        return temp
    # todo: override delete() to fully remove from hard disk
    # todo: override create to chmod
    # todo: override create with compression util


class File(AvishanModel):
    file = models.FileField(blank=True)
    private_fields = ('date_created',)
    list_display = ('file', 'date_created')

    def __str__(self):
        return self.file.name


class UserGroup(AvishanModel):
    title = models.CharField(max_length=255, unique=True)
    token_valid_seconds = models.IntegerField(default=0)
    is_base_group = models.BooleanField(default=False)

    list_display = ('title', 'is_base_group', 'token_valid_seconds')

    # todo only one is_base_group can have

    def __str__(self):
        return self.title


class User(AvishanModel):
    phone = models.CharField(max_length=255, unique=True)
    first_name = models.CharField(max_length=255, blank=True)
    last_name = models.CharField(max_length=255, blank=True)

    is_active = models.BooleanField(default=False)
    have_profile = models.BooleanField(default=False)

    date_updated = models.DateTimeField(blank=True, null=True)

    compact_fields = ('first_name', 'last_name', 'phone')
    list_display = ('phone', '__str__', 'is_active')
    private_fields = ['id', 'have_profile', 'date_updated']

    def __str__(self):
        if self.first_name or self.last_name:
            return self.first_name + " " + self.last_name
        return self.phone

    def is_in_group(self, user_group: UserGroup) -> bool:
        try:
            UserUserGroup.get(avishan_raise_exception=True, user=self, user_group=user_group)
            return True
        except UserUserGroup.DoesNotExist:
            return False

    def add_to_user_group(self, user_group: UserGroup):
        try:
            UserUserGroup.get(
                avishan_raise_exception=True,
                user=self,
                user_group=user_group
            )
        except UserUserGroup.DoesNotExist:
            UserUserGroup.create(
                user=self,
                user_group=user_group,
            )


class UserUserGroup(AvishanModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_user_groups')
    user_group = models.ForeignKey(UserGroup, on_delete=models.CASCADE, related_name='user_user_groups')
    is_logged_in = models.BooleanField(default=False)
    date_last_login = models.DateTimeField(blank=True, null=True)
    date_last_used = models.DateTimeField(blank=True, null=True)

    list_display = ('user', 'user_group', 'date_last_login', 'date_last_used')

    def __str__(self):
        return str(self.user) + ' - ' + str(self.user_group)


class KavenegarSMS(AvishanModel):
    STATUS_TYPES = {
        'in_queue': 1,
        'scheduled': 2,
        'sent_to_telecom': 4,
        'sent_to_telecom2': 5,
        'failed': 6,
        'delivered': 10,
        'undelivered': 11,
        'user_canceled_sms': 13,
        'user_blocked_sms': 14,
        'invalid_id': 100
    }
    receptor = models.CharField(max_length=255)
    message = models.TextField()
    template_title = models.CharField(max_length=255, null=True, blank=True)

    http_status_code = models.CharField(max_length=255,
                                        blank=True)  # todo: https://kavenegar.com/rest.html#result-general
    message_id = models.CharField(max_length=255, blank=True)
    status = models.IntegerField(default=-1, blank=True)
    sender = models.CharField(max_length=255, blank=True)
    date = models.DateTimeField(blank=True, null=True)
    cost = models.IntegerField(blank=True, default=0)

    list_display = ('receptor', 'message', 'template_title', 'http_status_code', 'status', 'cost')

    def __str__(self):
        return self.receptor

    @classmethod
    def class_plural_snake_case_name(cls) -> str:
        return 'kavenegar_smses'


class ActivationCode(AvishanModel):
    code = models.CharField(max_length=255)
    user_group = models.ForeignKey(UserGroup, on_delete=models.CASCADE, null=True, blank=True)
    kavenegar_sms = models.ForeignKey(KavenegarSMS, on_delete=models.CASCADE)

    list_display = ('kavenegar_sms', 'code')

    def __str__(self):
        return self.kavenegar_sms.receptor + ' - ' + self.code


class ExceptionRecord(AvishanModel):
    class_title = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    user_group = models.ForeignKey(UserGroup, on_delete=models.SET_NULL, null=True, blank=True)
    status_code = models.IntegerField()
    request_url = models.TextField()
    request_method = models.CharField(max_length=255)
    request_data = models.TextField()
    request_headers = models.TextField(null=True)
    response = models.TextField()
    traceback = models.TextField()
    exception_args = models.TextField(null=True)
    checked = models.BooleanField(default=False)

    list_display = ('class_title', 'date_created', 'get_title', 'user', 'checked')
    list_filter = ('class_title', 'user', 'request_url', 'checked')
    date_hierarchy = 'date_created'

    @property
    def get_title(self):
        # try:
        if self.exception_args:
            return self.exception_args
        return self.response
    # except:
    #     return 'UNKNOWN'
# todo: create a request copy model. to keep request full data
