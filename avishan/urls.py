from django.urls import path
from .views import *


urlpatterns = [
    path('base/<str:model_plural_name>/', models_store),
    path('base/<str:model_plural_name>/<str:function_name>/', model_function_caller),
    path('base/<str:model_plural_name>/<int:object_id>/', models_detail),
    path('base/<str:model_plural_name>/<int:object_id>/<str:function_name>/', object_function_caller),

]
