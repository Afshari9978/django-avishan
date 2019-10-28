from typing import List, Type

from django.db import models


class AvishanModel(models.Model):
    # todo 0.2.1: use manager or simply create functions here?
    class Meta:
        abstract = True

    """
    Django admin default values. Set this for all inherited models
    """
    date_hierarchy = None
    list_display = None
    list_filter = []
    list_max_show_all = 300
    list_per_page = 100
    raw_id_fields = []
    readonly_fields = []
    search_fields = []

    @classmethod
    def class_name(cls) -> str:
        return cls.__name__

    @classmethod
    def class_snake_case_name(cls) -> str:
        import re
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', cls.class_name())
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    @staticmethod
    def find_non_abstract_models(app_name: str = None) -> List[Type['AvishanModel']]:
        return [x for x in AvishanModel.find_models(app_name) if x._meta.abstract is False]

    @staticmethod
    def find_models(app_name: str = None) -> List[Type['AvishanModel']]:
        if not app_name:
            total = AvishanModel.__subclasses__()
            for item in total[:]:
                if len(item.__subclasses__()) > 0:
                    total += item.__subclasses__()  # todo 0.2.0: should be recursive
            return list(set(total))
        return [x for x in AvishanModel.find_models() if x._meta.app_label == app_name]
