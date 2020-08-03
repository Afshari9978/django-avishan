from django.db import models

from avishan.models import *


class AuthenticationType(AvishanModel):
    user_user_group = models.OneToOneField(UserUserGroup, on_delete=models.CASCADE, help_text='Target UserUserGroup')
    last_used = models.DateTimeField(default=None, blank=True, null=True, help_text='Last time user sent request')
    last_login = models.DateTimeField(default=None, blank=True, null=True, help_text='Last time user logged in')
    last_logout = models.DateTimeField(default=None, blank=True, null=True, help_text='Last time user logged out')

    export_ignore = True

    django_admin_raw_id_fields = [user_user_group]
    django_admin_list_display = ['key', user_user_group, last_used, last_login, last_logout]
    django_admin_list_filter = [user_user_group]
    django_admin_search_fields = ['key']

    class Meta:
        abstract = True

    @classmethod
    def direct_callable_methods(cls):
        return super().direct_callable_methods() + [
            DirectCallable(
                model=cls,
                target_name='login',
                response_json_key=cls.class_snake_case_name(),
                method=DirectCallable.METHOD.POST,
                authenticate=False
            )
        ]

    @classmethod
    def _register(cls, user_user_group: UserUserGroup, key: str, **kwargs) -> 'AuthenticationType':
        from avishan.exceptions import AuthException

        try:
            key_item = cls.key_field().related_model.get(key=key)
        except cls.key_field().related_model.DoesNotExist:
            key_item = cls.key_field().related_model.create(key)
        try:
            cls.objects.get(**{
                'key': key_item,
                'user_user_group__user_group': user_user_group.user_group
            })
            raise AuthException(AuthException.DUPLICATE_AUTHENTICATION_IDENTIFIER)
        except cls.DoesNotExist:
            pass

        creation_dict = {
            **{
                'user_user_group': user_user_group,
                'key': key_item,
            },
            **kwargs
        }

        return cls.create(**creation_dict)

    @classmethod
    def login(cls, key: str, user_group_title: str = None, **kwargs) -> 'AuthenticationType':
        from avishan.exceptions import AuthException

        try:
            if not user_group_title:
                found_object: KeyValueAuthentication = cls.objects.get(
                    key=cls.key_field().related_model.get(key=key))
            else:
                found_object: KeyValueAuthentication = cls.objects.get(**{
                    'key': cls.key_field().related_model.get(key=key),
                    'user_user_group__user_group__title': user_group_title
                })

        except cls.DoesNotExist:
            raise AuthException(AuthException.ACCOUNT_NOT_FOUND)
        except cls.MultipleObjectsReturned:
            raise AuthException(AuthException.MULTIPLE_CONNECTED_ACCOUNTS)
        kwargs['found_object'] = found_object
        kwargs['submit_login'] = True

        cls._login_post_check(kwargs)

        if kwargs['submit_login']:
            found_object._submit_login()
        return found_object

    @classmethod
    def _login_post_check(cls, kwargs):
        """
        Checks for post login
        :param kwargs:
        :type kwargs:
        """
        pass

    def _submit_login(self):
        self.last_login = timezone.now()
        self.last_used = None
        self.last_logout = None
        self.save()
        self.populate_current_request()

    def _submit_logout(self):
        self.last_logout = timezone.now()
        self.save()
        current_request['authentication_object'] = None
        current_request['add_token'] = False

    def populate_current_request(self):
        current_request['base_user'] = self.user_user_group.base_user
        current_request['user_group'] = self.user_user_group.user_group
        current_request['user_user_group'] = self.user_user_group
        current_request['authentication_object'] = self
        if current_request['language'] is None:
            current_request['language'] = self.user_user_group.base_user.language
        current_request['add_token'] = True

    @classmethod
    def key_field(cls) -> models.ForeignKey:
        raise NotImplementedError()


class KeyValueAuthentication(AuthenticationType):
    hashed_password = models.CharField(max_length=255, blank=True, null=True, default=None, help_text='Hashed password')

    to_dict_private_fields = [hashed_password]

    class Meta:
        abstract = True

    @classmethod
    def register(cls, user_user_group: UserUserGroup, key: str, password: Optional[str] = None) -> \
            Union['EmailPasswordAuthenticate', 'PhonePasswordAuthenticate']:

        data = {
            'user_user_group': user_user_group,
            'key': key
        }

        if password is not None:
            data['hashed_password'] = cls._hash_password(password)

        return cls._register(**data)

    # noinspection PyMethodOverriding
    @classmethod
    def login(cls, key: str, password: str, user_group_title: str = None, **kwargs) -> 'KeyValueAuthentication':
        return super().login(key=key, user_group_title=user_group_title, password=password, **kwargs)

    def add_password(self, password: str) -> bool:
        if self.hashed_password is None:
            self.hashed_password = self._hash_password(password)
            self.save()
            return True
        return False

    @classmethod
    def key_field(cls) -> Union[models.ForeignKey, models.Field]:
        return cls.get_field('key')

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
    def _login_post_check(cls, kwargs):
        from avishan.exceptions import AuthException

        if not cls._check_password(kwargs['password'], kwargs['found_object'].hashed_password):
            raise AuthException(AuthException.INCORRECT_PASSWORD)


class EmailPasswordAuthenticate(KeyValueAuthentication):
    key = models.ForeignKey(Email, on_delete=models.CASCADE, related_name='password_authenticates',
                            help_text='Related Email object')


class PhonePasswordAuthenticate(KeyValueAuthentication):
    key = models.ForeignKey(Phone, on_delete=models.CASCADE, related_name='password_authenticates',
                            help_text='Related Phone object')


class OtpAuthentication(AuthenticationType):
    code = models.CharField(max_length=255, blank=True, null=True, help_text='Code sent to user')
    date_sent = models.DateTimeField(null=True, blank=True, default=None, help_text='Date code sent to user')
    tried_codes = models.TextField(blank=True, default="", help_text='Incorrect user tried codes')

    to_dict_private_fields = [code, tried_codes, date_sent]

    class Meta:
        abstract = True

    @classmethod
    def register(cls, user_user_group: UserUserGroup, key: str) -> 'OtpAuthentication':

        data = {
            'user_user_group': user_user_group,
            'key': key
        }
        return cls._register(**data)

    @classmethod
    def login(cls, key: str, user_group_title: str = None, **kwargs) -> 'OtpAuthentication':
        return super().login(key=key, user_group_title=user_group_title, verify=False)

    @classmethod
    def _login_post_check(cls, kwargs):
        from avishan.exceptions import ErrorMessageException, AuthException

        found_object: PhoneOtpAuthenticate = kwargs['found_object']
        if isinstance(found_object, PhoneOtpAuthenticate):
            gap = get_avishan_config().POA_VERIFICATION_GAP_SECONDS
        else:
            raise NotImplementedError()

        if not kwargs.get('verify', False):
            kwargs['submit_login'] = False
            if found_object.date_sent and (timezone.now() - found_object.date_sent).total_seconds() < gap:
                raise ErrorMessageException(AvishanTranslatable(
                    EN='Verification code sent recently, Please try again later',
                    FA='برای ارسال مجدد کد، کمی صبر کنید'
                ))
            if get_avishan_config().ASYNC_AVAILABLE:
                from avishan.tasks import async_phone_otp_authentication_send_otp_code
                async_phone_otp_authentication_send_otp_code.delay(poa_id=found_object.id)
            else:
                found_object.send_otp_code()

        else:
            code = kwargs['entered_code']
            if not found_object._check_entered_code(code):
                raise AuthException(AuthException.INCORRECT_PASSWORD)
            if found_object.last_login is None:
                current_request['status_code'] = status.HTTP_201_CREATED
            found_object.code = None
            found_object.date_sent = None
            found_object.tried_codes = ""
            found_object.save()
            if found_object.key.date_verified is None:
                found_object.key.date_verified = timezone.now()
                found_object.key.save()

    @classmethod
    def verify(cls, key: str, entered_code: str, user_group: UserGroup = None) -> 'OtpAuthentication':

        try:
            cls.key_field().related_model.get(key=key)
        except cls.key_field().related_model.DoesNotExist:
            cls.key_field().related_model.create(key)

        return super().login(
            key=key,
            user_group=user_group,
            verify=True,
            entered_code=entered_code
        )

    def send_otp_code(self):
        self.code = self.create_otp_code()
        self.date_sent = timezone.now()
        self.tried_codes = ""
        self.save()

    def _check_entered_code(self, entered_code: str) -> bool:
        from avishan.exceptions import ErrorMessageException

        if isinstance(self, PhoneOtpAuthenticate):
            valid_seconds = get_avishan_config().POA_VERIFICATION_VALID_SECONDS
        else:
            raise NotImplementedError()

        if self.code is None:
            raise ErrorMessageException(AvishanTranslatable(
                EN='Code not found for this account',
                FA='برای این حساب کدی پیدا نشد'
            ))
        if (timezone.now() - self.date_sent).total_seconds() > valid_seconds:
            self.code = None
            self.save()
            raise ErrorMessageException(AvishanTranslatable(
                EN='Code Expired',
                FA='کد منقضی شده است'
            ))

        if self.code != entered_code:
            self.tried_codes += f"{entered_code}\n"
            self.save()
            return False

        return True

    @classmethod
    def create_otp_code(cls) -> str:
        if cls._meta.model is PhoneOtpAuthenticate:
            length = get_avishan_config().POA_VERIFICATION_CODE_LENGTH
        else:
            raise NotImplementedError()

        return str(random.randint(10 ** (length - 1), 10 ** length - 1))

    @classmethod
    def key_field(cls) -> Union[models.Field, models.ForeignKey]:
        return cls.get_field('key')


class PhoneOtpAuthenticate(OtpAuthentication):
    key = models.ForeignKey(Phone, on_delete=models.CASCADE, related_name='otp_authenticates',
                            help_text='Related Phone object')

    def send_otp_code(self):
        from avishan.exceptions import ErrorMessageException
        super().send_otp_code()

        if get_avishan_config().KAVENEGAR_SMS_ENABLE:
            self.key.send_sms(
                template=get_avishan_config().KAVENEGAR_DEFAULT_TEMPLATE,
                token=self.code
            )
        else:
            raise ErrorMessageException(AvishanTranslatable(
                EN='SMS Provider not found. Enable in "SMS Providers" avishan config section'
            ))


class VisitorKey(AuthenticationType):
    key = models.CharField(max_length=255, unique=True, help_text='Random generated key')

    django_admin_list_display = key,
    django_admin_search_fields = key,

    @classmethod
    def create(cls, key: str) -> 'VisitorKey':
        return super().create(key=key)

    @classmethod
    def key_field(cls) -> models.Field:
        return cls.get_field('key')

    @staticmethod
    def create_key() -> str:
        import secrets
        return secrets.token_urlsafe(get_avishan_config().VISITOR_KEY_LENGTH)

    @classmethod
    def register(cls, user_user_group: UserUserGroup) -> 'VisitorKey':

        key = cls.create_key()
        while True:
            try:
                cls.get(key=key)
                key = cls.create_key()
            except cls.DoesNotExist:
                break

        data = {
            'user_user_group': user_user_group,
            'key': key,
        }

        return cls.objects.create(**data)

    @classmethod
    def login(cls, key: str, user_group_title: str = None) -> 'VisitorKey':
        from avishan.exceptions import AuthException

        try:
            found_object = cls.objects.get(
                **{
                    'key': key,
                    "user_user_group__user_group__title": user_group_title
                }
            )
        except cls.DoesNotExist:
            raise AuthException(AuthException.ACCOUNT_NOT_FOUND)

        found_object._submit_login()
        return found_object

    def __str__(self):
        return self.key
