from django.urls import path, re_path

from avishan.views.class_based import AvishanModelApiView, PasswordHash
from avishan.configure import get_avishan_config
from avishan.views.function_based import avishan_doc, avishan_chayi_create, avishan_redoc

urlpatterns = [
    path(f'{get_avishan_config().AVISHAN_URLS_START}'
         f'/doc',
         avishan_doc),
    path(f'{get_avishan_config().AVISHAN_URLS_START}'
         f'/chayi',
         avishan_chayi_create),
    path(f'{get_avishan_config().AVISHAN_URLS_START}'
         f'/redoc',
         avishan_redoc),
    path(f'{get_avishan_config().AVISHAN_URLS_START}'
         f'/hash_password/<str:password>',
         PasswordHash.as_view()),
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
