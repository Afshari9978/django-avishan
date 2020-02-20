from django.urls import path

from avishan.views.function_based import avishan_hash_password, avishan_doc

from avishan.views.class_based import AvishanModelApiView, AvishanView
from avishan.configure import get_avishan_config
from avishan.views.panel_views import AvishanPanelView, AvishanPanelLoginView, AvishanPanelListView

urlpatterns = [
    path(f'{get_avishan_config().AVISHAN_URLS_START}/hash_password/<str:password>', avishan_hash_password),
    path(f'{get_avishan_config().AVISHAN_URLS_START}/<str:model_plural_name>', AvishanModelApiView.as_view()),
    path(f'{get_avishan_config().AVISHAN_URLS_START}/<str:model_plural_name>/<int:model_item_id>',
         AvishanModelApiView.as_view()),
    path(f'{get_avishan_config().AVISHAN_URLS_START}/<str:model_plural_name>/<str:model_function_name>',
         AvishanModelApiView.as_view()),
    path(
        f'{get_avishan_config().AVISHAN_URLS_START}/<str:model_plural_name>/<int:model_item_id>/<str:model_function_name>',
        AvishanModelApiView.as_view()
    ),
    path('api/doc', avishan_doc),
    path('test_cbv', AvishanView.as_view()),
    path(f'{get_avishan_config().PANEL_ROOT}', AvishanPanelView.as_view()),
    path(f'{get_avishan_config().PANEL_ROOT}/login', AvishanPanelLoginView.as_view()),
    path(f'{get_avishan_config().PANEL_ROOT}/list', AvishanPanelListView.as_view())
]
