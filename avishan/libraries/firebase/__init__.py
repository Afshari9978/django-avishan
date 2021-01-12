from requests import post, Response
from avishan.configure import get_avishan_config

FIREBASE_SERVER_TOKEN = get_avishan_config().FIREBASE_SERVER_TOKEN


def send_firebase_data_message(data: dict, to_key: str, server_key: str = FIREBASE_SERVER_TOKEN) -> Response:
    return post(
        url='https://fcm.googleapis.com/fcm/send',
        json={
            "data": data,
            'to': to_key,
            "android": {
                "priority": "high"
            },
        },
        headers={
            'Authorization': f'key={server_key}'}

    )


def send_firebase_notification(title: str, body: str, to_key: str, server_key: str = FIREBASE_SERVER_TOKEN):
    return post(
        url='https://fcm.googleapis.com/fcm/send',
        json={
            "notification": {
                "title": title,
                "body": body
            },
            'to': to_key,
            "android": {
                "priority": "high"
            },
        },
        headers={
            'Authorization': f'key={server_key}'}

    )


def send_firebase_data_and_notification(
        title: str,
        body: str,
        data: str,
        to_key: str,
        server_key: str = FIREBASE_SERVER_TOKEN,
        print_data: bool = False):
    data = {
            "notification": {
                "title": title,
                "body": body
            },
            'data': data,
            'to': to_key,
            "android": {
                "priority": "high"
            },
        }
    if print_data:
        print(data)
    return post(
        url='https://fcm.googleapis.com/fcm/send',
        json=data,
        headers={
            'Authorization': f'key={server_key}'}

    )
