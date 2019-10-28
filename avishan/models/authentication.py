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
        pass  # todo 0.2.0

    @property
    def last_login(self) -> Optional[datetime]:
        """
        Last login comes from this user user group authorization types.
        """
        pass  # todo 0.2.0


class UserDevice(AvishanModel):
    user_user_group = models.ForeignKey(UserUserGroup, on_delete=models.CASCADE, related_name='devices')
    date_created = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True, blank=True, default=None)
    used_count = models.BigIntegerField(default=0)


class AuthenticationType(AvishanModel):
    user_user_group = models.OneToOneField(UserUserGroup, on_delete=models.CASCADE)
    last_used = models.DateTimeField(default=None, blank=True, null=True)
    last_login = models.DateTimeField(default=None, blank=True, null=True)
    is_login = models.BooleanField(default=None, null=True, blank=True)

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
        # todo: raise appropriate AuthExceptions 0.2.0

    @classmethod
    def do_password_login(cls, key_name: str, key_value: str, value_name: str,
                          value_value: str) -> 'AuthenticationType':
        """
        Doing login action in key-value aspect
        :param key_name: identifier name: username, email
        :param key_value: identifier value: afshari9978, afshari9978@gmail.com
        :param value_name: checking name: password, code, passphrase
        :param value_value: checking value (unhashed): 123465
        """
        from avishan.exceptions import AuthException
        from avishan.utils import populate_current_request

        try:
            found_object = cls.objects.get(**{key_name: key_value})
        except cls.DoesNotExist:
            raise AuthException(AuthException.ACCOUNT_NOT_FOUND)
        if not cls.check_password(value_value, found_object.__getattribute__(value_name)):
            # todo 0.2.3: count incorrect enters with time, ban after some time
            raise AuthException(AuthException.INCORRECT_PASSWORD)

        found_object.last_login = BchDatetime().to_datetime()
        found_object.is_login = True
        found_object.save()

        populate_current_request(found_object)

        return found_object

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash entered password
        :param password:
        :return: hashed password in string
        """
        import bcrypt
        return bcrypt.hashpw(password.encode('utf8'), bcrypt.gensalt()).decode('utf8')

    @staticmethod
    def check_password(password: str, hashed_password: str) -> bool:
        """
        compares password with hashed instance.
        :param password:
        :param hashed_password:
        :return: True if match
        """
        import bcrypt
        return bcrypt.checkpw(password.encode('utf8'), hashed_password.encode('utf8'))


class EmailPasswordAuthenticate(AuthenticationType):
    email = models.CharField(max_length=255, unique=True)
    password = models.CharField(max_length=255, blank=True, null=True, default=None)

    @staticmethod
    def register(user_user_group: UserUserGroup, email: str, password: str, **kwargs):
        pass  # todo 0.2.0

    @staticmethod
    def login(**kwargs):
        pass  # todo 0.2.0


class PhonePasswordAuthenticate(AuthenticationType):
    phone = models.CharField(max_length=255, unique=True)
    password = models.CharField(max_length=255, blank=True, null=True, default=None)

    @staticmethod
    def register(user_user_group: UserUserGroup, phone: str, password: str) -> 'PhonePasswordAuthenticate':
        """
        Register phone-password authentication type for user. If there be errors, will raise straight.
        :param user_user_group:
        :param phone:
        :param password: un-hashed password.
        :return: created
        """
        from avishan.exceptions import AuthException
        try:
            PhonePasswordAuthenticate.objects.get(
                phone=phone
            )
            raise AuthException(AuthException.DUPLICATE_AUTHENTICATION_IDENTIFIER)
        except PhonePasswordAuthenticate.DoesNotExist:
            pass
        created = PhonePasswordAuthenticate.objects.create(
            user_user_group=user_user_group,
            phone=phone,
            password=AuthenticationType.hash_password(password)
        )
        return created  # todo 0.2.2: put validator on phone/password

    @staticmethod
    def login(phone: str, password: str) -> 'PhonePasswordAuthenticate':
        return PhonePasswordAuthenticate.do_password_login('phone', phone, 'password', password)
