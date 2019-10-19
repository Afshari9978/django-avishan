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
    base_user = models.ForeignKey(BaseUser, on_delete=models.CASCADE, related_name='user_user_groups')
    user_group = models.ForeignKey(UserGroup, on_delete=models.CASCADE, related_name='user_user_groups')
    last_login = models.DateTimeField(null=True, blank=True, default=None)
    date_created = models.DateTimeField(auto_now_add=True)
    """Only active users can use system. This field checks on every request"""
    is_active = models.BooleanField(default=True, blank=True)
    is_logged_in = models.BooleanField(default=True, blank=True)

    @property
    def last_used(self) -> Optional[datetime]:
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


class PhonePasswordAuthenticate(AvishanModel):
    user_user_group = models.OneToOneField(UserUserGroup, on_delete=models.CASCADE, related_name='phone_password_auth')
    phone = models.CharField(max_length=255, unique=True)
    password = models.CharField(max_length=255, blank=True, null=True, default=None)
