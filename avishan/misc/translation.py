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
        try:
            from avishan import current_request
            if self.__dict__[current_request['lang']] is not None:
                return self.__dict__[current_request['lang']]
            raise ValueError
        except:
            try:
                if self.__dict__[get_avishan_config().LANGUAGE] is not None:
                    return self.__dict__[get_avishan_config().LANGUAGE]
                raise ValueError
            except:
                if len(self.__dict__.keys()) > 0:
                    return list(self.__dict__.values())[0]
                from avishan.exceptions import ErrorMessageException
                raise ErrorMessageException(str(AvishanTranslatable(EN='Not translated string', FA='رشته ترجمه نشده')))
