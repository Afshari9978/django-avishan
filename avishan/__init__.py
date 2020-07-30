import threading

thread_storage = threading.local()
thread_storage.current_request = {}

current_request = thread_storage.current_request
