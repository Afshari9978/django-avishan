from typing import List, Type, Tuple, Optional

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

    @classmethod
    def app_name(cls) -> str:
        return cls._meta.app_label

    @staticmethod
    def find_non_abstract_models(app_name: str = None) -> List[Type['AvishanModel']]:
        return [x for x in AvishanModel.find_models(app_name) if x._meta.abstract is False]

    @staticmethod
    def find_models(app_name: str = None) -> List[Type['AvishanModel']]:

        def get_sub_classes(parent):
            subs = [parent]
            for child in parent.__subclasses__():
                subs += get_sub_classes(child)
            return subs

        total = []
        if not app_name:
            for model in AvishanModel.__subclasses__():
                total += get_sub_classes(model)
            return list(set(total))

        return [x for x in AvishanModel.find_models() if x._meta.app_label == app_name]

    @staticmethod
    def find_model_with_class_name(class_name: str) -> Optional[Type['AvishanModel']]:
        for item in AvishanModel.find_models():
            if item.class_name() == class_name:
                return item
        return None

    @classmethod
    def create_or_update(cls, fixed_kwargs: dict, new_additional_kwargs: dict) -> Tuple[Type['AvishanModel'], bool]:
        """
        Create object if doesnt exists. Else update it
        :param fixed_kwargs: key values to find object in db
        :param new_additional_kwargs: new changing kwargs
        :return: found/created object and True if created, False if found
        """
        try:
            found = cls.objects.get(**fixed_kwargs)
            for key, value in new_additional_kwargs.items():
                found.__setattr__(key, value)
            found.save()
            return found, False
        except cls.DoesNotExist:
            return cls.objects.create(
                **{**fixed_kwargs, **new_additional_kwargs}
            ), True
