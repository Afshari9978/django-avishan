import random

from django.http import JsonResponse

from .utils.model_functions import find_models, find_model_by_plural_name
from .decorators import AvishanDecorator
from .exceptions import ErrorMessageException, AuthException
from .utils.validator_functions import validate_phone_number
from avishan_config import SMS_CODE_LENGTH, SMS_RESEND_ALLOWED_SECONDS, SMS_SIGNIN_TEMPLATE, SMS_SIGNUP_TEMPLATE, \
    SMS_CODE_VALID_SECONDS
from .models import *
from .utils.bch_datetime import BchDatetime
from .utils import status
from .utils.auth_functions import verify_user, sign_in_user
from .utils.data_functions import send_template_sms


@AvishanDecorator()
def check_user_phone(request, role, phone):
    from avishan_wrapper import current_request
    phone = validate_phone_number(phone)
    current_request['user_group'] = UserGroup.get(title=role)
    if not current_request['user_group']:
        raise AuthException(AuthException.UNAUTHORIZED_ROLE)

    # todo kevenegar takes too long
    # todo email and username and etc...
    current_request['response']['phone'] = phone
    code = str(random.randrange(10 ** (SMS_CODE_LENGTH - 1), 10 ** SMS_CODE_LENGTH - 1))
    try:
        old_activation_code = ActivationCode.objects.get(kavenegar_sms__receptor=phone,
                                                         user_group=current_request['user_group'])
    except ActivationCode.DoesNotExist:
        old_activation_code = None

    if old_activation_code and (
            BchDatetime() - BchDatetime(old_activation_code.date_created)).total_seconds() < SMS_RESEND_ALLOWED_SECONDS:
        raise ErrorMessageException('برای ارسال مجدد پیامک، کمی بعد تلاش کنید',
                                    status_code=status.HTTP_408_REQUEST_TIMEOUT)
    if old_activation_code:
        old_activation_code.delete()

    try:
        user = User.objects.get(phone=phone)
        verify_user(user, current_request['user_group'])

        send_template_sms(phone, SMS_SIGNIN_TEMPLATE, code)

    except User.DoesNotExist:
        user = None
        if not current_request['user_group'].is_base_group:
            raise ErrorMessageException('حساب کاربری پیدا نشد')

        send_template_sms(phone, SMS_SIGNUP_TEMPLATE, code)

    if user and user.have_profile:
        return JsonResponse(current_request['response'])
    return JsonResponse(current_request['response'], status=status.HTTP_201_CREATED)


@AvishanDecorator()
def check_user_code(request, role, phone, code):
    from avishan_wrapper import current_request
    phone = validate_phone_number(phone)
    current_request['response']['phone'] = phone
    current_request['user_group'] = UserGroup.get(title=role)
    if not current_request['user_group']:
        raise AuthException(AuthException.WTF)

    try:
        activation_code = ActivationCode.objects.get(kavenegar_sms__receptor=phone,
                                                     user_group=current_request['user_group'])
    except ActivationCode.DoesNotExist:
        raise ErrorMessageException('کد ورود برای این شماره پیدا نشد، لطفا مجددا کد دریافت کنید')

    if (BchDatetime() - BchDatetime(activation_code.date_created)).total_seconds() > SMS_CODE_VALID_SECONDS:
        activation_code.delete()
        raise ErrorMessageException('زمان اعتبار این کد به اتمام رسیده، لطفا مجددا کد دریافت کنید')

    if activation_code.code != code:
        raise ErrorMessageException('کد وارد شده اشتباه است')

    created = False
    try:
        user = User.get(avishan_raise_exception=True, phone=phone)
        current_request['user'] = user
    except User.DoesNotExist:
        if not current_request['user_group'].is_base_group:
            raise ErrorMessageException('حساب کاربری پیدا نشد')

        # todo har user natoone be grooh haye dige add kone
        user = User.objects.create(
            phone=phone,
            is_active=True,
        )
        current_request['user'] = user
        created = True
        user.add_to_user_group(current_request['user_group'])

    activation_code.delete()
    sign_in_user(current_request['user'], current_request['user_group'])

    if created or not user.have_profile:
        return JsonResponse(current_request['response'], status=status.HTTP_201_CREATED)
    return JsonResponse(current_request['response'])


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
