from django.db import models

from avishan.models import AvishanModel
from avishan.models.authentication import BaseUser


class Image(AvishanModel):
    file = models.ImageField(blank=True)
    base_user = models.ForeignKey(BaseUser, on_delete=models.SET_NULL, null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)


class Video(AvishanModel):
    pass  # todo 0.2.3


class File(AvishanModel):
    pass  # todo 0.2.1
