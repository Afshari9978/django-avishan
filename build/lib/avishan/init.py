from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist


def init():
    pass
    # try:
    #     get_user_model().objects.get(username='afshari9978')
    # except ObjectDoesNotExist:
    #     get_user_model()._default_manager.db_manager('default').create_superuser(**{
    #         'username': 'afshari9978',
    #         'email': 'afshari9978@gmail.com',
    #         'password': '',
    #         'first_name': 'Morteza',
    #         'last_name': 'Afshari'
    #     })
