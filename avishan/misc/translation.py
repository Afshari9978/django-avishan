from avishan.configure import get_avishan_config


class AvishanTranslatable:
    EN = None
    FA = None

    # todo 0.2.5: can we translate something by default? like "title", "icon", etc...
    def __init__(self, **kwargs):
        """
        translatable texts
        :param kwargs: keys like: FA, EN
        """

        for key, value in kwargs.items():
            self.__setattr__(key.upper(), value)

    def __str__(self):
        from avishan import current_request
        from avishan.exceptions import ErrorMessageException

        try:
            if self.__dict__[current_request['language']] is not None:
                return self.__dict__[current_request['language']]
            raise ValueError
        except:
            raise ErrorMessageException(str(AvishanTranslatable(EN='Not translated string', FA='رشته ترجمه نشده')))
