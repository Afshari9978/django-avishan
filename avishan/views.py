from django.db import models
from django.http import JsonResponse

from avishan import current_request
from avishan.decorators import AvishanApiView, AvishanTemplateView
from avishan.exceptions import ErrorMessageException
from avishan.misc.translation import AvishanTranslatable
from avishan.models import AvishanModel, AuthenticationType


# todo fix cors motherfucker
@AvishanApiView(methods=['GET', 'POST'], track_it=True)
def avishan_model_store(request, model_plural_name):
    model = AvishanModel.get_model_by_plural_name(model_plural_name)
    if not model:
        raise ErrorMessageException('Entered model name not found')

    if request.method == 'GET':
        search_text = None
        url_params = request.GET.copy()
        if url_params.get('s', False):
            search_text = url_params['s']
            del url_params['s']
        filter_kwargs = {}
        for filter_key, filter_value in url_params.items():
            if isinstance(model.get_field(filter_key), (models.ForeignKey, models.OneToOneField)):
                filter_kwargs[filter_key] = {'id': filter_value}
            else:
                filter_kwargs[filter_key] = filter_value
        total = model.search(model.filter(**filter_kwargs), search_text)
        current_request['response'][model.class_plural_snake_case_name()] = [item.to_dict() for item in total]

    elif request.method == 'POST':
        current_request['response'][model.class_snake_case_name()] = model.create(
            **request.data[model.class_snake_case_name()]
        ).to_dict()

    return JsonResponse(current_request['response'])


@AvishanApiView(methods=['GET', 'PUT', 'DELETE'], track_it=True)
def avishan_model_details(request, model_plural_name, item_id):
    model = AvishanModel.get_model_by_plural_name(model_plural_name)
    if not model:
        raise ErrorMessageException('Entered model name not found')

    item = model.get(avishan_raise_400=True, id=item_id)

    if request.method == 'GET':
        current_request['response'][model.class_snake_case_name()] = item.to_dict()

    elif request.method == 'PUT':
        current_request['response'][model.class_snake_case_name()] = item.update(
            **request.data[model.class_snake_case_name()]).to_dict()

    elif request.method == 'DELETE':
        current_request['response'][model.class_snake_case_name()] = item.remove()

    return JsonResponse(current_request['response'])


@AvishanApiView(methods=['POST', 'GET', 'PUT'], track_it=True)
def avishan_model_function_caller(request, model_plural_name, function_name):
    # todo add parameter 'function_caller_methods' to each model and check them here
    model = AvishanModel.get_model_by_plural_name(model_plural_name)
    if not model:
        raise ErrorMessageException('Entered model name not found')

    try:
        target_function = getattr(model, function_name)
    except AttributeError:
        raise ErrorMessageException(AvishanTranslatable(
            EN=f'Requested method not found in model {model.class_name()}'
        ))
    if request.method == 'POST' or request.method == 'PUT':
        current_request['response'] = {**target_function(**current_request['request'].data),
                                       **current_request['response']}
    elif request.method == 'GET':
        current_request['response'] = {**target_function(), **current_request['response']}
    return JsonResponse(current_request['response'])


@AvishanApiView(methods=['POST', 'GET', 'PUT'], track_it=True)
def avishan_item_function_caller(request, model_plural_name, item_id, function_name):
    model = AvishanModel.get_model_by_plural_name(model_plural_name)
    if not model:
        raise ErrorMessageException('Entered model name not found')

    item = model.get(avishan_raise_400=True, id=item_id)

    try:
        target_function = getattr(item, function_name)
    except AttributeError:
        raise ErrorMessageException(AvishanTranslatable(
            EN=f'Requested method not found in record {item}'
        ))

    if request.method == 'POST' or request.method == 'PUT':
        current_request['response'] = {**target_function(**current_request['request'].data),
                                       **current_request['response']}
    elif request.method == 'GET':
        current_request['response'] = {**target_function(), **current_request['response']}

    return JsonResponse(current_request['response'])


@AvishanApiView(authenticate=False, track_it=True)
def avishan_hash_password(request, password: str):
    # todo change it to accept get / post request
    current_request['response'] = {
        'hashed_password': AuthenticationType._hash_password(password)
    }
    return JsonResponse(current_request['response'])


@AvishanTemplateView(authenticate=False)
def avishan_doc(request):
    from avishan.libraries.openapi3 import create_openapi_object
    import json
    data = json.dumps(create_openapi_object('Snappion API Documentation', '1.0.0'))
    from django.shortcuts import render
    return render(request, 'swagger.html', context={'data': data})
