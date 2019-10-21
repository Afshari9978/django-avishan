import threading

thread_storage = threading.local()
thread_storage.current_request = {}


def add_data_to_response(field: str, data):
    current_request['response'][field] = data
    current_request['discard_wsgi_response'] = True


current_request = thread_storage.current_request
