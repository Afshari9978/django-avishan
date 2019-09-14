import json
import pprint

from django.http import JsonResponse

from .utils.data_functions import save_traceback
from .exceptions import AvishanException
from avishan_wrapper import current_request


class AvishanDecorator(object):
    def __init__(self):

        pass

    def __call__(self, view_function):
        # todo we should have method checker
        def wrapper(*args, **kwargs):
            request = current_request['request']

            if request.method != 'GET':
                from django.http.request import RawPostDataException
                try:
                    if len(request.body) > 0:
                        request.data = json.loads(request.body.decode('utf-8'))
                        # todo: hich kodoom az key ha nabayad ba "avishan*_" shoroo beshe
                    else:
                        request.data = {}
                except RawPostDataException:
                    request.data = {}

            try:
                return view_function(*args, **kwargs)
            except Exception as e:
                save_traceback()
                current_request['exception'] = e
                return JsonResponse({}, status=567)

        return wrapper


class AvishanCalculateTime(object):
    def __init__(self):
        pass

    def __call__(self, view_function):
        from .utils.bch_datetime import BchDatetime

        def wrapper(*args, **kwargs):
            start_time = BchDatetime()

            result = view_function(*args, **kwargs)

            end_time = BchDatetime()
            current_request['execution_time'] = end_time.to_unix_timestamp('microsecond') - start_time.to_unix_timestamp(
                'microsecond')

            return result

        return wrapper


class AvishanPrintRequestBody(object):
    def __init__(self):
        pass

    def __call__(self, view_function):

        def wrapper(*args, **kwargs):
            print("++++++++++++++++++++ " + view_function.__name__ + " ++++++++++++++++++++")
            print("***** REQUEST *****")
            request = current_request['request']
            if request.method != 'GET':
                try:
                    pprint.pprint(request.data)
                except AttributeError:
                    if len(request.body) > 0:
                        request.data = json.loads(request.body.decode('utf-8'))
                    else:
                        request.data = {}
                    pprint.pprint(request.data)

            try:
                result = view_function(*args, **kwargs)
            except AvishanException as e:
                print("***** RESPONSE *****")
                print("-------------------- " + view_function.__name__ + " --------------------")
                save_traceback()
                raise e

            print("***** RESPONSE *****")
            if isinstance(result, JsonResponse):
                response = json.loads(result.content.decode('utf-8'))
                pprint.pprint(response)
            print("-------------------- " + view_function.__name__ + " --------------------")

            return result

        return wrapper

# todo: part by part execution time calculator decorator
