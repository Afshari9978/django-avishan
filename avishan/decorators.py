class AvishanView:
    def __init__(self, methods=None):
        if methods is None:
            methods = ['GET']
        self.methods = methods

    def __call__(self, view_function):

        def wrapper(*args, **kwargs):
            from . import current_request
            if current_request['request'].method not in self.methods:
                pass  # todo http method check
            try:
                result = view_function(*args, **kwargs)
            except:
                pass  # todo handle exception catcher

            return result

        return wrapper


class AvishanApiView(AvishanView):
    def __init__(self, methods=None):
        self.type = 'api'
        super().__init__(methods=methods)


class AvishanTemplateView(AvishanView):
    def __init__(self, methods=None):
        self.type = 'template'
        super().__init__(methods=methods)


class AvishanCalculate:
    # todo: execution time
    pass
