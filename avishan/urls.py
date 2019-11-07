from django.urls import path

from avishan.views import avishan_model_store, avishan_model_details, avishan_model_function_caller, \
    avishan_item_function_caller, avishan_template_dashboard, avishan_template_list, avishan_template_create, \
    avishan_template_view, avishan_template_edit, avishan_template_delete, avishan_template_login, \
    avishan_template_logout, avishan_root_redirect

urlpatterns = [
    path('api/av1/<str:model_plural_name>/', avishan_model_store),
    path('api/av1/<str:model_plural_name>/<int:item_id>', avishan_model_details),
    path('api/av1/<str:model_plural_name>/<str:function_name>/', avishan_model_function_caller),
    path('api/av1/<str:model_plural_name>/<int:item_id>/<str:function_name>/', avishan_item_function_caller),

    path('', avishan_root_redirect),
    path('panel', avishan_template_dashboard),
    path('panel/logout', avishan_template_logout),
    path('panel/login', avishan_template_login, name='panel_login'),
    path('panel/<str:model_plural_name>', avishan_template_list),
    path('panel/<str:model_plural_name>/create', avishan_template_create),
    path('panel/<str:model_plural_name>/view/<int:item_id>', avishan_template_view),
    path('panel/<str:model_plural_name>/edit/<int:item_id>', avishan_template_edit),
    path('panel/<str:model_plural_name>/delete/<int:item_id>', avishan_template_delete),
]
