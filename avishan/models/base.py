from django.db import models

from avishan.models import AvishanModel


class Image(AvishanModel):
    from avishan.models.authentication import BaseUser

    file = models.ImageField(blank=True, null=True)
    base_user = models.ForeignKey(BaseUser, on_delete=models.SET_NULL, null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)


class Video(AvishanModel):
    pass  # todo 0.2.3


class File(AvishanModel):
    from avishan.models.authentication import BaseUser

    file = models.FileField(blank=True, null=True)
    base_user = models.ForeignKey(BaseUser, on_delete=models.SET_NULL, null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
