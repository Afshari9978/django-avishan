from datetime import datetime
from typing import Optional

from django.db import models

from avishan.misc.bch_datetime import BchDatetime
from . import AvishanModel


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
    def last_used(self) -> Optional[datetime]:
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
    def last_login(self) -> Optional[datetime]:
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
