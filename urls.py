from django.urls import path
from .views import *

urlpatterns = [
    path('auth/check_phone/<str:role>/<str:phone>/', check_user_phone),
    path('auth/check_code/<str:role>/<str:phone>/<str:code>/', check_user_code),

    path('base/<str:model_plural_name>/', avishan_model_store),
    path('base/<str:model_plural_name>/<int:id>/', avishan_model_detail),
]
