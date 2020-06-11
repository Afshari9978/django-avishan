from typing import Union, Type, List

from django.core.management import BaseCommand


# no import from avishan here


class AvishanConfigure:

    @staticmethod
    def command_line_checkup(management_command):
        # todo
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
    NOT_MONITORED_STARTS: List[str] = ['/admin', '/static', '/media', '/favicon.ico']
    IGNORE_TRACKING_STARTS: List[str] = []
    AVISHAN_URLS_START = 'api/av1'
    JWT_KEY: str = None
    USE_JALALI_DATETIME: bool = False
    LANGUAGE = LANGUAGES.EN
    NEW_USERS_LANGUAGE = None
    EMAIL_VERIFICATION_GAP_SECONDS = 5 * 60
    EMAIL_VERIFICATION_VALID_SECONDS = 30 * 60
    EMAIL_VERIFICATION_TRIES_COUNT = 3
    EMAIL_VERIFICATION_CODE_LENGTH = 6
    SMS_SIGN_IN_TEMPLATE = 'signin'
    SMS_SIGN_UP_TEMPLATE = 'signup'

    # POA
    POA_VERIFICATION_CODE_LENGTH = 4
    POA_VERIFICATION_VALID_SECONDS = 10 * 60

    # PhoneVerification
    PHONE_VERIFICATION_GAP_SECONDS = 90
    PHONE_VERIFICATION_TRIES_COUNT = 3
    PHONE_MINIMUM_LENGTH = 10

    # Faker
    FAKER_LOCALE: str = 'fa_IR'
    FAKER_SEED: int = None

    #  Firebase
    FIREBASE_SERVER_TOKEN: Union[str, dict] = ''

    # VisitorToken
    VISITOR_KEY_LENGTH = 40

    # Panel
    PANEL_ROOT = 'panel'
    PANEL_TITLE = 'پنل مدیریت'
    PANEL_ENABLE_LOG: bool = False  # todo
    PANEL_LOGIN_CLASS_NAME = 'PhonePasswordAuthenticate'
    PANEL_LOGIN_USER_GROUP_TITLE = 'admin'
    PANEL_TRANSLATION_DICT: dict = {}

    # open api
    REQUEST_COMMON_URL_PARAMETERS = [{
        "name": 'language',
        "in": 'query',
        "description": 'set language for this request',
        "required": False,
    }]

    # Kavenegar
    KAVENEGAR_API_TOKEN: str = None

    # Django Email
    EMAIL_SENDER_ADDRESS: str = None  # none if not using it

    # Mailgun
    MAILGUN_DOMAIN_NAME: str = None
    MAILGUN_API_KEY: str = None  # none if not using it
    MAILGUN_SENDER_ADDRESS: str = None
    MAILGUN_SENDER_NAME: str = None

    # Neshan
    NESHAN_API_KEY: str = None

    # Chayi
    CHAYI_PROJECT_PACKAGE: str = None
    CHAYI_MODEL_FILE_IMPORTS: str = None

    @classmethod
    def on_startup(cls):
        """
        This method will be called anytime server starts. But just the method from get_avishan_config() result.
        """
        pass

    @classmethod
    def on_request(cls):
        """
        This method called for any request, just before Avishan middleware starts calling get_response()
        """
        pass

    @classmethod
    def get_otp_users(cls) -> List[Type]:
        return []

    @classmethod
    def create_or_update_user_group(cls, title: str, token_valid_seconds: int):
        from avishan.models import UserGroup
        return UserGroup.create_or_update(
            fixed_kwargs={'title': title},
            new_additional_kwargs={
                'token_valid_seconds': token_valid_seconds,
            }
        )

    @classmethod
    def get_country_mobile_numbers_data(cls) -> List[dict]:
        return [
            {
                'name': 'Iran',
                'dialing_code': '98',
                'mobile_number_length': 10,
                'mobile_providers': {
                    'mtn': ['901', '902', '903', '904', '905', '930', '933', '935', '936', '937', '938', '939'],
                    'mci': ['91', '990', '991', '992', '993', '994'],
                    'rightel': ['920', '921', '922'],
                    'mtce': ['931'],
                    'taliya': ['932'],
                    'kish-tci': ['934'],
                    'aptel': ['99910', '99911', '99913'],
                    'azartel': ['99914'],
                    'samantel': ['99999', '99998', '99997', '99996'],
                    'lotustel': ['9990'],
                    'shatel': ['99810', '99811', '99812', '99814'],
                    'ariantel': ['9998'],
                    'anarestan': ['9944']
                }
            }
        ]


def get_avishan_config() -> Union[Type[AvishanConfigFather]]:
    for sub_class in AvishanConfigFather.__subclasses__():
        sub_class: Type[AvishanConfigFather]
        return sub_class
    return AvishanConfigFather
