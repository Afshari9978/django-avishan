from django.urls import path, re_path

from avishan.views.class_based import AvishanModelApiView, PasswordHash
from avishan.configure import get_avishan_config
from avishan.views.function_based import avishan_doc, avishan_chayi_create
from avishan.views.panel_views import AvishanPanelErrorPage, AvishanPanelLoginPage, \
    AvishanPanelLogoutPage, AvishanPanelModelPage, AvishanPanelTestPage, AvishanPanelDashboardPage

urlpatterns = [
    path(f'{get_avishan_config().AVISHAN_URLS_START}'
         f'/doc',
         avishan_doc),
    path(f'{get_avishan_config().AVISHAN_URLS_START}'
         f'/chayi',
         avishan_chayi_create),
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
    ),
    path(f'{get_avishan_config().PANEL_ROOT}',
         AvishanPanelDashboardPage.as_view()),
    path(f'{get_avishan_config().PANEL_ROOT}'
         f'/error',
         AvishanPanelErrorPage.as_view()),
    path(f'{get_avishan_config().PANEL_ROOT}'
         f'/test',
         AvishanPanelTestPage.as_view()),
    path(f'{get_avishan_config().PANEL_ROOT}'
         f'/login',
         AvishanPanelLoginPage.as_view()),
    path(f'{get_avishan_config().PANEL_ROOT}'
         f'/logout',
         AvishanPanelLogoutPage.as_view()),
    re_path(get_avishan_config().PANEL_ROOT + r'/.*',
            AvishanPanelModelPage.as_view()),
]
