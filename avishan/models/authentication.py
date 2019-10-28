from datetime import datetime
from typing import Optional

from django.db import models

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

    """Check if this group users can access to their specific space in this ways"""
    authenticate_with_email_password = models.BooleanField(default=False)
    authenticate_with_phone_password = models.BooleanField(default=False)


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
        Login with entered data. Also do on-login action.
        on-login actions:
            -
        :param kwargs: entered credential like username, email, password and etc.
        :return: return true if login accepted
        """
        raise NotImplementedError()
        # todo: raise appropriate AuthExceptions 0.2.0

    @staticmethod
    def check_login(user_user_group: UserUserGroup):
        """
        Checks for authorizations for login and set values needed for login
        :param user_user_group:
        :return:
        """

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
    def check_password(password, hashed_password) -> bool:
        """
        compares password with hashed instance.
        :param password:
        :param hashed_password:
        :return: True if match
        """
        import bcrypt
        return bcrypt.checkpw(password, hashed_password)


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
    def register(user_user_group: UserUserGroup, phone: str, password: str):
        """
        Register phone-password authentication type for user.
        :param user_user_group:
        :param phone:
        :param password: un-hashed password.
        :return:
        """
        pass  # todo 0.2.0

    @staticmethod
    def login(phone: str, password: str) -> UserUserGroup:
        from avishan.exceptions import AuthException
        try:
            phone_password_authenticate = PhonePasswordAuthenticate.objects.get(
                phone=phone
            )
        except PhonePasswordAuthenticate.DoesNotExist:
            raise AuthException(AuthException.ACCOUNT_NOT_FOUND)
        if not AuthenticationType.check_password(password, phone_password_authenticate.password):
            # todo 0.2.3: count incorrect enters with time, ban after some time
            raise AuthException(AuthException.INCORRECT_PASSWORD)

        AuthenticationType.check_login(phone_password_authenticate.user_user_group)
        return phone_password_authenticate.user_user_group
