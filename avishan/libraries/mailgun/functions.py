from typing import List

from avishan.configure import get_avishan_config


def send_mail(recipient_list: List[str], subject: str, message: str, html_message: str = None):
    import requests
    data = {"from": f"{get_avishan_config().MAILGUN_SENDER_NAME} <{get_avishan_config().MAILGUN_SENDER_ADDRESS}>",
              "to": recipient_list,
              "subject": subject}
    if message:
        data['text'] = message
    if html_message:
        data['html'] = html_message

    return requests.post(
        f"https://api.mailgun.net/v3/{get_avishan_config().MAILGUN_DOMAIN_NAME}/messages",
        auth=("api", get_avishan_config().MAILGUN_API_KEY),
        data=data
    )
