from django.contrib import admin
from django.contrib.admin.sites import AlreadyRegistered

from .utils.model_functions import find_non_abstract_models

# todo auto add classes for admin
for model in find_non_abstract_models():
    model_admin_dict = {
        'date_hierarchy': model.date_hierarchy,
        'list_filter': model.list_filter,
        'list_max_show_all': model.list_max_show_all,
        'list_per_page': model.list_per_page,
        'raw_id_fields': model.raw_id_fields,
        'readonly_fields': model.readonly_fields,
        'search_fields': model.search_fields,
    }
    if model.list_display:
        model_admin_dict['list_display'] = model.list_display
    model_admin = type(model.class_snake_case_name() + "_admin", (admin.ModelAdmin,), model_admin_dict)
    try:
        admin.site.register(model, model_admin)
    except AlreadyRegistered:
        pass
