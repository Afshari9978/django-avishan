from avishan.configure import get_avishan_config
from crum import get_current_request


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
            if get_current_request().avishan.language is None:
                lang = get_avishan_config().LANGUAGE
            else:
                lang = get_current_request().avishan.language
            if lang.upper() in self.__dict__.keys() and self.__dict__[lang.upper()] is not None:
                return self.__dict__[lang.upper()]
        except:
            pass
        try:
            return list(self.__dict__.values())[0]
        except IndexError:
            return 'NOT_TRANSLATED_STRING'

    def __repr__(self):
        return str(self)
