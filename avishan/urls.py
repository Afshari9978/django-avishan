from django.urls import path

from avishan.views import avishan_model_store, avishan_model_details, avishan_model_function_caller, \
    avishan_item_function_caller, avishan_model_page_function_caller, avishan_item_page_function_caller, \
    avishan_hash_password

urlpatterns = [
    path('api/av1/hash_password/<str:password>', avishan_hash_password),
    path('api/av1/<str:model_plural_name>', avishan_model_store),
    path('api/av1/<str:model_plural_name>/<int:item_id>', avishan_model_details),
    path('api/av1/<str:model_plural_name>/<str:function_name>', avishan_model_function_caller),
    path('api/av1/<str:model_plural_name>/<int:item_id>/<str:function_name>', avishan_item_function_caller),
    path('api/av1/<str:model_plural_name>/pages/<str:function_name>', avishan_model_page_function_caller),
    path('api/av1/<str:model_plural_name>/<int:item_id>/pages/<str:function_name>', avishan_item_page_function_caller),
]
