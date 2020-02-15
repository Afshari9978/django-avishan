from django import template
from django.db import models

from avishan.models import AvishanModel

register = template.Library()


@register.filter
def translator(value: str) -> str:
    data = {
        'phone': 'شماره همراه',
        'email': 'ایمیل'
    }
    try:
        return data[value.lower()]
    except KeyError:
        return value
