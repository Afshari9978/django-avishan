class AvishanView:
    def __init__(self):
        pass

    def __call__(self, view_function):
        # todo http method check
        def wrapper(*args, **kwargs):

            try:
                result = view_function(*args, **kwargs)
            except:
                pass  # todo handle exception catcher

            return result

        return wrapper


class AvishanCalculate:
    # todo: execution time
    pass

