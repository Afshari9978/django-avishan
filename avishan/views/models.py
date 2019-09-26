from django.http import JsonResponse

from ..utils.model_functions import find_model_by_plural_name
from ..decorators import AvishanDecorator
from ..exceptions import ErrorMessageException


@AvishanDecorator()
def avishan_model_store(request, model_plural_name):
    from avishan_wrapper import current_request

    model = find_model_by_plural_name(model_plural_name)
    if not model:
        raise ErrorMessageException(f'AvishanError: Model not found')

    if request.method == 'GET':
        current_request['response'][model.class_plural_snake_case_name()] = [item.to_dict() for item in model.all()]

    elif request.method == 'POST':
        current_request['response'][model.class_snake_case_name()] = model.create(
            **request.data[model.class_snake_case_name()]
        ).to_dict()

    return JsonResponse(current_request['response'])


@AvishanDecorator()
def avishan_model_detail(request, model_plural_name, id):
    from avishan_wrapper import current_request
    # todo: check if model available, else raise error

    model = find_model_by_plural_name(model_plural_name)
    if not model:
        raise ErrorMessageException('AvishanError: Model not found')

    record = model.get(avishan_raise_400=True, id=id)

    if request.method == 'GET':
        current_request['response'][model.class_snake_case_name()] = record.to_dict()

    elif request.method == 'PUT':
        current_request['response'][model.class_snake_case_name()] = record.update(
            **request.data[model.class_snake_case_name()]).to_dict()

    elif request.method == 'DELETE':
        current_request['response'][model.class_snake_case_name()] = record.remove()

    return JsonResponse(current_request['response'])
