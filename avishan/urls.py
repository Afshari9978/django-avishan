from django.urls import path
from .views.models import *

urlpatterns = [

    path('base/<str:model_plural_name>/', avishan_model_store),
    path('base/<str:model_plural_name>/<int:id>/', avishan_model_detail),
]
