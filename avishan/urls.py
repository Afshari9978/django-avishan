from django.urls import path

from avishan.views import avishan_model_store, avishan_model_details, avishan_model_function_caller, \
    avishan_item_function_caller

urlpatterns = [
    path('base/<str:model_plural_name>/', avishan_model_store),
    path('base/<str:model_plural_name>/<int:item_id>', avishan_model_details),
    path('base/<str:model_plural_name>/<str:function_name>/', avishan_model_function_caller),
    path('base/<str:model_plural_name>/<int:item_id>/<str:function_name>/', avishan_item_function_caller),

]
