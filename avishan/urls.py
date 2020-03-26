from django.urls import path, re_path

from avishan.views.function_based import avishan_hash_password, avishan_doc

from avishan.views.class_based import AvishanModelApiView, AvishanView
from avishan.configure import get_avishan_config
from avishan.views.panel_views import AvishanPanelErrorPage, AvishanPanelPage, AvishanPanelLoginPage, \
    AvishanPanelLogoutPage, AvishanPanelModelPage, AvishanPanelTestPage

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
    path(f'{get_avishan_config().PANEL_ROOT}', AvishanPanelPage.as_view()),
    path(f'{get_avishan_config().PANEL_ROOT}/error', AvishanPanelErrorPage.as_view()),
    path(f'{get_avishan_config().PANEL_ROOT}/test', AvishanPanelTestPage.as_view()),
    path(f'{get_avishan_config().PANEL_ROOT}/login', AvishanPanelLoginPage.as_view()),
    path(f'{get_avishan_config().PANEL_ROOT}/logout', AvishanPanelLogoutPage.as_view()),
    re_path(get_avishan_config().PANEL_ROOT + r'/.*', AvishanPanelModelPage.as_view()),
]
