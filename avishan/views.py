from django.http import JsonResponse
from django.shortcuts import render, redirect

from avishan import current_request
from avishan.decorators import AvishanApiView, AvishanTemplateView
from avishan.exceptions import ErrorMessageException
from avishan.models import AvishanModel
from avishan_config import AvishanConfig


@AvishanApiView()
def avishan_model_store(request, model_plural_name):
    model = AvishanModel.get_model_by_plural_name(model_plural_name)
    if not model:
        raise ErrorMessageException(f'AvishanError: Model not found')

    if request.method == 'GET':
        current_request['response'][model.class_plural_snake_case_name()] = [item.to_dict() for item in model.all()]

    elif request.method == 'POST':
        current_request['response'][model.class_snake_case_name()] = model.create(
            **request.data[model.class_snake_case_name()]
        ).to_dict()

    return JsonResponse(current_request['response'])


@AvishanApiView()
def avishan_model_details(request, model_plural_name, item_id):
    model = AvishanModel.get_model_by_plural_name(model_plural_name)
    if not model:
        raise ErrorMessageException('AvishanError: Model not found')

    item = model.get(avishan_raise_400=True, id=item_id)

    if request.method == 'GET':
        current_request['response'][model.class_snake_case_name()] = item.to_dict()

    elif request.method == 'PUT':
        current_request['response'][model.class_snake_case_name()] = item.update(
            **request.data[model.class_snake_case_name()]).to_dict()

    elif request.method == 'DELETE':
        current_request['response'][model.class_snake_case_name()] = item.remove()

    return JsonResponse(current_request['response'])


@AvishanApiView()
def avishan_model_function_caller(request, model_plural_name, function_name):
    model = AvishanModel.get_model_by_plural_name(model_plural_name)
    if not model:
        raise ErrorMessageException('AvishanError: Model not found')

    target_function = getattr(model, function_name)
    current_request['response'][function_name] = target_function(**current_request['request']['data'])
    return JsonResponse(current_request['response'])


@AvishanApiView()
def avishan_item_function_caller(request, model_plural_name, item_id, function_name):
    model = AvishanModel.get_model_by_plural_name(model_plural_name)
    if not model:
        raise ErrorMessageException('AvishanError: Model not found')

    item = model.get(avishan_raise_400=True, id=item_id)

    target_function = getattr(item, function_name)
    current_request['response'][function_name] = target_function(**current_request['request']['data'])
    return JsonResponse(current_request['response'])
