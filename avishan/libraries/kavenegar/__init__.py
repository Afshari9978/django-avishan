from typing import Optional, Union, List

import requests

from avishan.configure import get_avishan_config
from avishan.exceptions import ErrorMessageException
from avishan.misc.translation import AvishanTranslatable
from avishan.models import Phone


# todo 0.2.2 full functions https://kavenegar.com/rest.html


def send_raw_sms(phone: Union[Phone, List[Phone]], text: str,
                 api_key: Optional[str] = get_avishan_config().KAVENEGAR_API_TOKEN):
    receptor = ""
    if isinstance(phone, Phone):
        receptor = phone.key
    else:
        for item in phone:
            receptor += item.key + ","
        if len(phone) > 0:
            receptor = receptor[:-1]
    if len(receptor) == 0:
        raise ErrorMessageException(message=AvishanTranslatable(
            EN='Empty receptor numbers',
            FA='لیست دریافت کننده‌ها خالی است'
        ))

    data = {
        'receptor': receptor,
        'message': text
    }

    response = requests.post(
        url=f"https://api.kavenegar.com/v1/{api_key}/sms/send.json",
        data=data
    )
    if response.status_code != 200:
        print(response.text)


def send_template_sms(phone: Phone, template_name: str, token: str, token2: str = None, token3: str = None,
                      api_key: Optional[str] = get_avishan_config().KAVENEGAR_API_TOKEN):
    data = {
        'receptor': phone.key,
        'template': template_name,
        'token': token
    }
    if token2 is not None:
        data['token2'] = token2
    if token3 is not None:
        data['token3'] = token3

    response = requests.post(
        url=f"https://api.kavenegar.com/v1/{api_key}/verify/lookup.json",
        data=data
    )
    if response.status_code != 200:
        print(response.text)
