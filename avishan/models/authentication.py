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
    # todo: raise appropriate exception for exceeding unique rule here.
    base_user = models.ForeignKey(BaseUser, on_delete=models.CASCADE, related_name='user_user_groups')
    user_group = models.ForeignKey(UserGroup, on_delete=models.CASCADE, related_name='user_user_groups')

    """Last time user entered credentials to login using this method"""
    last_login = models.DateTimeField(null=True, blank=True, default=None)

    """Date this link created between user and user group"""
    date_created = models.DateTimeField(auto_now_add=True)

    """
    Each token have address to models.authentication.UserUserGroup object. If this fields become false, user cannot use 
    system with this role. "is_active" field on models.authentication.BaseUser will not override on this field. 
    """
    is_active = models.BooleanField(default=True, blank=True)

    """Checks for login/logout. If user never logged in throw this object, it will returns None"""
    is_logged_in = models.BooleanField(default=None, blank=True, null=True)

    @property
    def last_used(self) -> Optional[datetime]:
        """
        Last used datetime. it will caught throw user devices. If never used, returns None
        """
        pass  # todo


class UserDevice(AvishanModel):
    user_user_group = models.ForeignKey(UserUserGroup, on_delete=models.CASCADE, related_name='devices')
    date_created = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True, blank=True, default=None)
    used_count = models.BigIntegerField(default=0)


class EmailPasswordAuthenticate(AvishanModel):
    user_user_group = models.OneToOneField(UserUserGroup, on_delete=models.CASCADE, related_name='email_password_auth')
    email = models.CharField(max_length=255, unique=True)
    password = models.CharField(max_length=255, blank=True, null=True, default=None)

    @staticmethod
    def register(email: str, password: str):
        pass  # todo

    @staticmethod
    def register_new_user(user_group: UserGroup, email: str, password: str):
        """
        Check for uniques. and create new user.
        :return:
        """
        pass

    def have_password(self):
        return not self.password


class PhonePasswordAuthenticate(AvishanModel):
    user_user_group = models.OneToOneField(UserUserGroup, on_delete=models.CASCADE, related_name='phone_password_auth')
    phone = models.CharField(max_length=255, unique=True)
    password = models.CharField(max_length=255, blank=True, null=True, default=None)

    @staticmethod
    def login(phone: str, password: str) -> Optional['PhonePasswordAuthenticate']:
        try:
            return PhonePasswordAuthenticate.objects.get(
                phone=phone,
                password=password
            )
        # todo: raise true exceptions
        except PhonePasswordAuthenticate.DoesNotExist:
            return None


class AuthenticationKind:

    @staticmethod
    def register(user_user_group: UserUserGroup, **kwargs):
        raise NotImplementedError()

    def pending_registration(self) -> bool:
        """
        checks for pending registrations
        :return: false if registered completely
        """
        raise NotImplementedError()

    @staticmethod
    def login(**kwargs):
        """
        login with entered data.
        :param kwargs: entered credential like username, email, password and etc.
        :return: return true if login accepted
        """
        raise NotImplementedError()
        # todo: raise appropriate AuthExceptions
