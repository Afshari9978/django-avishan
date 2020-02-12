from typing import Union, Type, List

from django.core.management import BaseCommand


# no import from avishan here

class AvishanConfigure:

    @staticmethod
    def command_line_checkup(management_command):
        # AvishanConfigure.check_for_config_file(management_command)
        AvishanConfigure.check_django_settings(management_command)

    @staticmethod
    def check_avishan_config_file():
        project_config = None
        for sub_class in AvishanConfigFather.__subclasses__():
            if project_config is not None:
                raise ValueError('Multiple implementation of AvishanConfigFather class found')
            project_config = sub_class

        if project_config is None:
            raise ValueError('AvishanConfig class not found. Run "python manage.py avishan_configure" command')

    @staticmethod
    def create_avishan_config_file():
        f = open('avishan_config.py', 'w+')

        f.writelines((
            'class AvishanConfig(AvishanConfigFather):\n',
            "    pass\n"
        ))
        f.close()

    @staticmethod
    def check_for_config_file(management_command: BaseCommand = None):
        from avishan.configure import AvishanConfigFather, AvishanConfigure

        project_config = None
        for sub_class in AvishanConfigFather.__subclasses__():
            if project_config is not None:
                message = 'Multiple implementation of AvishanConfigFather class found'
                management_command.stdout.write(management_command.style.ERROR(message))
                return
            project_config = sub_class

        if not project_config:
            AvishanConfigure.create_avishan_config_file()
            message = 'Successfully created config file. run again to check it.'
            management_command.stdout.write(management_command.style.SUCCESS(message))
        else:
            AvishanConfigure.check_avishan_config_file()

    @staticmethod
    def check_django_settings(management_command):
        from avishan.utils import find_file
        print(find_file('settings.py', '.'), '*')


class AvishanConfigFather:
    class LANGUAGES:
        FA = 'FA'
        EN = 'EN'

    MONITORED_APPS_NAMES: List[str] = []
    NOT_MONITORED_STARTS = []
    JWT_KEY = ''
    KAVENEGAR_API_TOKEN: str = None
    USE_JALALI_DATETIME: bool = True
    LANGUAGE = LANGUAGES.EN
    EMAIL_SENDER_ADDRESS: str = None
    EMAIL_VERIFICATION_GAP_SECONDS = 10
    EMAIL_VERIFICATION_VALID_SECONDS = 200
    EMAIL_VERIFICATION_TRIES_COUNT = 3
    EMAIL_VERIFICATION_CODE_LENGTH = 4
    SMS_SIGNIN_TEMPLATE = 'signin'
    SMS_SIGNUP_TEMPLATE = 'signup'
    PHONE_VERIFICATION_GAP_SECONDS = 10
    PHONE_VERIFICATION_VALID_SECONDS = 200
    PHONE_VERIFICATION_TRIES_COUNT = 1
    PHONE_VERIFICATION_CODE_LENGTH = 4

    def check(self):
        pass


def get_avishan_config() -> Union[Type[AvishanConfigFather]]:
    for sub_class in AvishanConfigFather.__subclasses__():
        sub_class: Type[AvishanConfigFather]
        return sub_class
    return AvishanConfigFather
