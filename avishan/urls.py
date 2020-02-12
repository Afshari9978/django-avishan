from django.urls import path

from avishan.views.function_based import avishan_hash_password, avishan_doc

from avishan.views.class_based import AvishanModelApiView, AvishanView

urlpatterns = [
    path('api/av1/hash_password/<str:password>', avishan_hash_password),
    path('api/av1/<str:model_plural_name>', AvishanModelApiView.as_view()),
    path('api/av1/<str:model_plural_name>/<int:model_item_id>', AvishanModelApiView.as_view()),
    path('api/av1/<str:model_plural_name>/<str:model_function_name>', AvishanModelApiView.as_view()),
    path(
        'api/av1/<str:model_plural_name>/<int:model_item_id>/<str:model_function_name>',
        AvishanModelApiView.as_view()
    ),
    path('api/doc', avishan_doc),
    path('test_cbv', AvishanView.as_view())
]
