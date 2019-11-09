from django.http import JsonResponse
from django.shortcuts import render, redirect

from avishan import current_request
from avishan.decorators import AvishanApiView, AvishanTemplateView
from avishan.exceptions import ErrorMessageException
from avishan.models import AvishanModel
from avishan_config import AvishanConfig


@AvishanApiView()
def avishan_model_store(request, model_plural_name):
    model = AvishanModel.find_model_by_plural_name(model_plural_name)
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
    model = AvishanModel.find_model_by_plural_name(model_plural_name)
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
    model = AvishanModel.find_model_by_plural_name(model_plural_name)
    if not model:
        raise ErrorMessageException('AvishanError: Model not found')

    target_function = getattr(model, function_name)
    current_request['response'][function_name] = target_function(**current_request['request']['data'])
    return JsonResponse(current_request['response'])


@AvishanApiView()
def avishan_item_function_caller(request, model_plural_name, item_id, function_name):
    model = AvishanModel.find_model_by_plural_name(model_plural_name)
    if not model:
        raise ErrorMessageException('AvishanError: Model not found')

    item = model.get(avishan_raise_400=True, id=item_id)

    target_function = getattr(item, function_name)
    current_request['response'][function_name] = target_function(**current_request['request']['data'])
    return JsonResponse(current_request['response'])


@AvishanTemplateView(authenticate=False)
def avishan_root_redirect(request):
    return redirect('/panel', permanent=True)


@AvishanTemplateView(authenticate=False)
def avishan_template_login(request):
    if request.method == 'POST':
        phone = request.POST['phone']
        password = request.POST['password']

        user = AvishanConfig.USER_MODEL.login(phone, password)
        if user:
            current_request['user'] = user
            return redirect('/', permanent=True)
    context = {
        'fields': AvishanConfig.TEMPLATE_LOGIN_AUTHENTICATE_TYPE.admin_fields(),
        'fields_verbose_name': AvishanConfig.TEMPLATE_LOGIN_AUTHENTICATE_TYPE.admin_fields_verbose_name(),
        'header': AvishanConfig.PANEL_LOGIN_HEADER
    }
    return render(request, 'login.html', context=context)


@AvishanTemplateView()
def avishan_template_logout(request):
    current_request['authentication_object'].logout()
    return redirect(AvishanConfig.TEMPLATE_LOGIN_URL, permanent=True)


@AvishanTemplateView()
def avishan_template_dashboard(request):
    context = {
        'models': AvishanModel.get_available_admin_models()
    }
    # todo 0.2.4: check for all panel needed variables. like admin_name...
    return render(request, 'pages/index.html', context=context)


@AvishanTemplateView()
def avishan_template_list(request, model_plural_name):
    model = AvishanModel.find_model_by_plural_name(model_plural_name)
    if not model:
        raise ErrorMessageException(f'AvishanError: Model not found')
    context = {
        'filter': model.admin_filters(),
        'list_display': model.admin_list_display(),
        'list_actions': model.admin_list_actions(),
        'items': model.all(),
        'models': AvishanModel.get_available_admin_models(),
        'model': model
    }

    return render(request, 'model_list.html', context=context)


@AvishanTemplateView()
def avishan_template_create(request, model_plural_name):
    pass


@AvishanTemplateView()
def avishan_template_view(request, model_plural_name, item_id):
    pass


@AvishanTemplateView()
def avishan_template_edit(request, model_plural_name, item_id):
    pass


@AvishanTemplateView()
def avishan_template_delete(request, model_plural_name, item_id):
    pass
