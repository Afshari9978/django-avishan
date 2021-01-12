from typing import List

from avishan.configure import get_avishan_config


def send_mail(recipient_list: List[str], subject: str, message: str):
    import requests

    return requests.post(
        f"https://api.mailgun.net/v3/{get_avishan_config().MAILGUN_DOMAIN_NAME}/messages",
        auth=("api", get_avishan_config().MAILGUN_API_KEY),
        data={"from": f"{get_avishan_config().MAILGUN_SENDER_NAME} <{get_avishan_config().MAILGUN_SENDER_ADDRESS}>",
              "to": recipient_list,
              "subject": subject,
              "text": message}
    )
