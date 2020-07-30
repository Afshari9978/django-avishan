from django import template
from django.db import models

from avishan.models import AvishanModel

register = template.Library()


@register.filter
def translator(value: str) -> str:
    data = {
        'phone': 'شماره همراه',
        'email': 'ایمیل',
    }
    try:
        return data[value.lower()]
    except KeyError:
        return value


@register.filter
def leading_zeros(value, desired_digits):
    """
    Given an integer, returns a string representation, padded with [desired_digits] zeros.
    """
    num_zeros = int(desired_digits) - len(str(value))
    padded_value = []
    while num_zeros >= 1:
        padded_value.append("0")
        num_zeros = num_zeros - 1
    padded_value.append(str(value))
    return "".join(padded_value)
