class Language:
    FA = 'FA'
    EN = 'EN'


class AvishanTranslatableText:

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
            return self.__dict__['EN']
            # todo hi dear. fuck you
        except KeyError:
            if len(self.__dict__.keys()) > 0:
                return list(self.__dict__.values())[0]
            from avishan.exceptions import ErrorMessageException
            raise ErrorMessageException(str(AvishanTranslatableText(EN='Not translated string', FA='رشته ترجمه نشده')))


def translatable(**kwargs) -> str:
    return str(AvishanTranslatableText(**kwargs))
