import datetime
import json
import random
from typing import Tuple

import requests
from django.core.paginator import Paginator
from django.db.models import QuerySet

from avishan_config import RECOMMEND_CODE_CHOICES, SMS_SIGNIN_TEMPLATE, KAVENEGAR_API_TOKEN, SMS_SIGNUP_TEMPLATE, \
    CHABOK_ACCESS_TOKEN, RECOMMEND_CODE_FROM_USER
from ..utils.bch_datetime import BchDatetime
from ..models import User, KavenegarSMS, ActivationCode


def is_number(input):
    try:
        float(input)
        return True
    except ValueError:
        pass

    try:
        import unicodedata
        unicodedata.numeric(input)
        return True
    except (TypeError, ValueError):
        pass

    return False


def has_numbers(input):
    return any(char.isdigit() for char in input)


def introduce_code_length() -> int:
    return 6


def create_introduce_code() -> str:
    while True:
        new_code = ''.join(
            random.choice(RECOMMEND_CODE_CHOICES) for _ in range(introduce_code_length()))
        try:
            # todo: mese adam
            User.objects.get(**{RECOMMEND_CODE_FROM_USER: new_code})
            continue
        except User.DoesNotExist:
            return new_code


def convert_to_fa_number(text):
    text = str(text)
    text = convert_to_en_number(text)
    array = ['۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹']
    result = ''
    for i in str(text):
        if i.isdigit():
            result = result + array[int(i)]
        else:
            result = result + i

    return result


def convert_to_en_number(text):
    text = str(text)
    result = ''
    array = ['۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹']
    for char in text:
        if char in array:
            result += str(array.index(char))
        else:
            result += char
    return result


def create_sms_transaction(user: User, amount: int):
    # if amount == 0:
    #     return
    #
    # amount = -amount
    # from core.models import SystemTransaction
    # last_transaction = SystemTransaction.objects.filter(is_sms=True, transaction__user=user).order_by('-date_created')
    # if len(last_transaction) > 0:
    #     last_transaction = last_transaction[0]
    #     last_transaction.transaction.amount += amount
    #     last_transaction.transaction.date_created = BchDatetime().to_datetime()
    #     last_transaction.transaction.save()
    # else:
    #     from core.models import Transaction
    #     SystemTransaction.objects.create(
    #         transaction=Transaction.objects.create(
    #             user=user, amount=amount, title='هزینه پیامک'
    #         ),
    #         is_sms=True
    #     )
    # todo
    pass


def send_template_sms(phone_number: str, template_title: str, token: str, token2: str = None,
                      token3: str = None) -> KavenegarSMS:
    from avishan_wrapper import current_request
    kavenegar_sms = KavenegarSMS.objects.create(
        receptor=phone_number,
        message=token + "|" + str(token2) + "|" + str(token3),
        template_title=template_title,
        date_created=BchDatetime().to_datetime()
    )

    if template_title == SMS_SIGNIN_TEMPLATE or template_title == SMS_SIGNUP_TEMPLATE:
        activation_code = ActivationCode.objects.create(
            code=token,
            user_group=current_request['user_group'],
            kavenegar_sms=kavenegar_sms,
            date_created=BchDatetime().to_datetime()
        )
    url = "https://api.kavenegar.com/v1/" + KAVENEGAR_API_TOKEN + "/verify/lookup.json"
    querystring = {"receptor": phone_number, "token": token, "template": template_title}
    if token2:
        querystring['token2'] = token2
    if token3:
        querystring['token3'] = token3
    response = requests.request("GET", url, data="", headers={}, params=querystring)

    data = json.loads((response.content).decode('utf8'))['entries'][0]
    kavenegar_sms.message_id = data['messageid']
    kavenegar_sms.message = data['message']
    kavenegar_sms.status = data['status']
    kavenegar_sms.sender = data['sender']
    kavenegar_sms.date = datetime.datetime.fromtimestamp(data['date'])
    kavenegar_sms.cost = data['cost']
    kavenegar_sms.http_status_code = response.status_code
    kavenegar_sms.save()

    return kavenegar_sms


def send_raw_sms(phone_number: str, message: str) -> KavenegarSMS:
    kavenegar_sms = KavenegarSMS.objects.create(
        receptor=phone_number,
        message=message,
        template_title=None
    )

    url = 'https://api.kavenegar.com/v1/' + KAVENEGAR_API_TOKEN + '/sms/send.json'
    response = requests.post(
        url,
        {'receptor': phone_number, 'message': message}
    )

    data = json.loads(response.content.decode('utf8'))['entries'][0]

    kavenegar_sms.message_id = data['messageid']
    kavenegar_sms.message = data['message']
    kavenegar_sms.status = data['status']
    kavenegar_sms.sender = str(data['sender'])
    kavenegar_sms.date = datetime.datetime.fromtimestamp(data['date'])
    kavenegar_sms.cost = data['cost']
    kavenegar_sms.http_status_code = response.status_code
    kavenegar_sms.save()

    try:
        user = User.objects.get(phone=phone_number, profile__use_sms_notification=True)
        create_sms_transaction(user, kavenegar_sms.cost // 10)
    except User.DoesNotExist:
        pass

    return kavenegar_sms


def send_chabok_push(phone_number: str, title: str, body: str):
    requests.post(
        'https://sandbox.push.adpdigital.com/api/push/notifyUser/' + phone_number
        + '?access_token=' + CHABOK_ACCESS_TOKEN,
        data={'title': title, 'body': body}
    )
    # todo check for error and raise exception


def add_query_set_to_response(query_set: QuerySet, response_dict: dict, key_name: str, request,
                              compact: bool = False, ) -> dict:
    response_dict[key_name] = []
    # if len(query_set) == 0:
    #     return response_dict
    # if len(request.search) > 0:
    #     sum_searched_query_set = query_set[0:0]
    #     for searchable_field in query_set[0].searchable_fields:
    #         sum_searched_query_set = sum_searched_query_set | query_set.filter(**{
    #             searchable_field + '__contains': request.search
    #         })
    #     sum_searched_query_set.distinct()
    #     query_set = sum_searched_query_set
    # todo: implement filter and sort & search

    paginated, count, total, have_next, have_previous = paginate(query_set, request.page, request.page_size)
    response_dict[key_name] = [item.to_dict(compact=compact) for item in paginated]

    response_dict['pagination'] = {
        'count': count,
        'total': total,
        'have_next': have_next,
        'have_previous': have_previous
    }

    return response_dict


def paginate(query_set: QuerySet, page: int = 0, page_size: int = 0) -> Tuple[
    QuerySet, int, int, bool, bool]:
    """
    it returns a tuple:
    paginated query_set, pages count, total objects count, have next, have previous
    """
    if page == 0:
        return (
            query_set, 1, query_set.count(), False, False
        )
    paginated = Paginator(query_set, page_size)

    return (
        paginated.page(page).object_list, paginated.num_pages, paginated.count, paginated.page(page).has_next(),
        paginated.page(page).has_previous()
    )


def diagram_js(days: int = 7, **kwargs) -> dict:
    # todo: set a rule for colors, unlimited
    dataset = {
        'backgroundColor': 'transparent', 'label': 'sample', 'borderColor': '#000000', 'data': []
    }
    data = {
        'labels': [],
        'datasets': []
    }

    for key, value in kwargs.items():
        temp = {**dataset}
        temp['label'] = key
        temp['borderColor'] = "#" + str(random.randint(0, 10)) + str(random.randint(0, 10)) + str(
            random.randint(0, 10)) + str(random.randint(0, 10)) + str(random.randint(0, 10)) + str(
            random.randint(0, 10))
        temp['model'] = value['model']
        temp['filter'] = value['filter']
        temp['added_filters'] = value.get('added_filters')
        data['datasets'].append(temp)

    end_datetime = BchDatetime().to_datetime()
    start_datetime = BchDatetime().load_time(datetime.time(0, 0, 0, 0)).to_datetime()

    for i in range(days):
        for dataset in data['datasets']:
            filter_dict = {
                dataset['filter'] + "__gte": start_datetime,
                dataset['filter'] + "__lt": end_datetime
            }
            if dataset['added_filters']:
                for item in dataset['added_filters']:
                    filter_dict[item[0]] = item[1]
            dataset['data'].append(
                dataset['model'].objects.filter(**filter_dict).count()
            )
        end_datetime = BchDatetime(start_datetime).to_datetime()
        start_datetime = start_datetime - datetime.timedelta(days=1)

    data['labels'].reverse()
    for dataset in data['datasets']:
        dataset['data'].reverse()
        del dataset['model']
    return data


# todo: yebar begirim ba filter, baad tooye for age lazem darim check konim hast behtare ya harbar get bezanim too for?


def save_traceback():
    import sys, traceback
    from avishan_wrapper import current_request
    exc_type, exc_value, exc_tb = sys.exc_info()
    tbe = traceback.TracebackException(
        exc_type, exc_value, exc_tb,
    )
    current_request['traceback'] = ''.join(tbe.format())
