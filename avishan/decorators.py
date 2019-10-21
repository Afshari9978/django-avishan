from avishan.utils import save_traceback_and_raise_exception


class AvishanView:
    def __init__(self, methods=None):
        if methods is None:
            methods = ['GET']
        self.methods = methods

    def __call__(self, view_function):

        def wrapper(*args, **kwargs):
            from .exceptions import AvishanException
            from . import current_request

            self.check()

            if current_request['request'].method not in self.methods:
                pass  # todo http method check
            try:
                result = view_function(*args, **kwargs)
            except AvishanException as e:
                save_traceback_and_raise_exception(e)
            except Exception as e:
                save_traceback_and_raise_exception(AvishanException(wrap_exception=e))

            return result

        return wrapper

    def check(self):
        raise NotImplementedError()


class AvishanApiView(AvishanView):
    def __init__(self, methods=None):
        self.type = 'api'
        super().__init__(methods=methods)

    def check(self):
        from . import current_request
        current_request['is_api'] = True


class AvishanTemplateView(AvishanView):
    def __init__(self, methods=None):
        self.type = 'template'
        super().__init__(methods=methods)

    def check(self):
        from . import current_request
        current_request['is_api'] = False


class AvishanCalculate:
    # todo: execution time
    pass
