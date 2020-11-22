from django.urls import path

from avishan.views.class_based import AvishanModelApiView, Redoc
from avishan.configure import get_avishan_config

urlpatterns = [
    path(f'{get_avishan_config().AVISHAN_URLS_START}'
         f'/redoc',
         Redoc.as_view()),
    path(f'{get_avishan_config().AVISHAN_URLS_START}'
         f'/<str:model_plural_name>',
         AvishanModelApiView.as_view()),
    path(f'{get_avishan_config().AVISHAN_URLS_START}'
         f'/<str:model_plural_name>/<int:model_item_id>',
         AvishanModelApiView.as_view()),
    path(f'{get_avishan_config().AVISHAN_URLS_START}'
         f'/<str:model_plural_name>/<str:model_function_name>',
         AvishanModelApiView.as_view()),
    path(
        f'{get_avishan_config().AVISHAN_URLS_START}'
        f'/<str:model_plural_name>/<int:model_item_id>/<str:model_function_name>',
        AvishanModelApiView.as_view()
    )
]
