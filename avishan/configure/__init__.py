from typing import Union, Type, List

from django.core.management import BaseCommand


# WARNING: no import from avishan here

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

    """
    Using datetime dict or string formatted dicts
    """
    USE_DATETIME_DICT: bool = True

    """
    Date & Datetime string formats
    """
    DATE_STRING_FORMAT = '%Y-%m-%d'
    DATETIME_STRING_FORMAT = '%Y-%m-%dT%H:%M:%S.%f'

    LANGUAGE = LANGUAGES.EN
    NEW_USERS_LANGUAGE = None
    ASYNC_AVAILABLE: bool = False

    # Email Providers
    DJANGO_SMTP_EMAIL_ENABLE = False
    MAILGUN_EMAIL_ENABLE = False

    # SMS Providers
    KAVENEGAR_SMS_ENABLE = False

    # Django SMTP
    DJANGO_SMTP_SENDER_ADDRESS: str = None

    # Mailgun
    MAILGUN_DOMAIN_NAME: str = None
    MAILGUN_API_KEY: str = None
    MAILGUN_SENDER_ADDRESS: str = None
    MAILGUN_SENDER_NAME: str = None

    # Kavenegar
    KAVENEGAR_API_TOKEN: str = None
    KAVENEGAR_SIGN_IN_TEMPLATE = None
    KAVENEGAR_SIGN_UP_TEMPLATE = None
    KAVENEGAR_DEFAULT_TEMPLATE = KAVENEGAR_SIGN_IN_TEMPLATE

    # Phone Verification
    PHONE_VERIFICATION_GAP_SECONDS = 90
    PHONE_VERIFICATION_TRIES_COUNT = 3
    PHONE_VERIFICATION_CODE_LENGTH = 4
    PHONE_VERIFICATION_VALID_SECONDS = 10 * 60
    PHONE_VERIFICATION_BODY_STRING = 'Your code is {code}'

    # Email Verification
    EMAIL_VERIFICATION_GAP_SECONDS = 4 * 60
    EMAIL_VERIFICATION_TRIES_COUNT = 3
    EMAIL_VERIFICATION_CODE_LENGTH = 6
    EMAIL_VERIFICATION_VALID_SECONDS = 30 * 60
    EMAIL_VERIFICATION_SUBJECT = 'Email Verification'
    """Only one of these two must be not-null"""
    EMAIL_VERIFICATION_BODY_STRING = 'Your code is {code}'
    EMAIL_VERIFICATION_BODY_HTML = None

    # Email Key Value Authentication
    EMAIL_KEY_VALUE_AUTHENTICATION_VERIFICATION_REQUIRED: bool = True
    EMAIL_KEY_VALUE_AUTHENTICATION_VERIFICATION_CODE_DOMAIN: str = 'ABCDEFGHKLMNPQRSTUVWXYZabcdefghkmnpqrstuvwxyz23456789'
    EMAIL_KEY_VALUE_AUTHENTICATION_VERIFICATION_CODE_LENGTH: int = 6
    EMAIL_KEY_VALUE_AUTHENTICATION_VERIFICATION_CODE_VALID_SECONDS: int = 2 * 60 * 60
    EMAIL_KEY_VALUE_AUTHENTICATION_VERIFICATION_CODE_GAP_SECONDS: int = 2 * 60 - 10
    EMAIL_KEY_VALUE_AUTHENTICATION_VERIFICATION_CODE_TRIES_COUNT: int = 8
    EMAIL_KEY_VALUE_AUTHENTICATION_RESET_PASSWORD_GAP_SECONDS: int = 2 * 60 - 10
    EMAIL_KEY_VALUE_AUTHENTICATION_RESET_PASSWORD_VALID_SECONDS: int = 2 * 60 * 60 - 10
    EMAIL_KEY_VALUE_AUTHENTICATION_RESET_PASSWORD_TOKEN_LENGTH: int = 4
    EMAIL_KEY_VALUE_AUTHENTICATION_RESET_PASSWORD_TOKEN_DOMAIN: str = '1234567890'
    EMAIL_KEY_VALUE_AUTHENTICATION_RESET_PASSWORD_SUBJECT: str = 'Email Verification Reset Password'
    EMAIL_KEY_VALUE_AUTHENTICATION_RESET_PASSWORD_BODY: str = 'Reset password token is {token}'
    EMAIL_KEY_VALUE_AUTHENTICATION_RESET_PASSWORD_HTML_BODY: str = None

    # Phone Key Value Authentication
    PHONE_KEY_VALUE_AUTHENTICATION_VERIFICATION_REQUIRED: bool = True
    PHONE_KEY_VALUE_AUTHENTICATION_VERIFICATION_CODE_DOMAIN: str = '1234567890'
    PHONE_KEY_VALUE_AUTHENTICATION_VERIFICATION_CODE_LENGTH: int = 4
    PHONE_KEY_VALUE_AUTHENTICATION_VERIFICATION_CODE_VALID_SECONDS: int = 15 * 60
    PHONE_KEY_VALUE_AUTHENTICATION_VERIFICATION_CODE_GAP_SECONDS: int = 2 * 60 - 10
    PHONE_KEY_VALUE_AUTHENTICATION_VERIFICATION_CODE_TRIES_COUNT: int = 4
    PHONE_KEY_VALUE_AUTHENTICATION_RESET_PASSWORD_GAP_SECONDS: int = 2 * 60 - 10
    PHONE_KEY_VALUE_AUTHENTICATION_RESET_PASSWORD_VALID_SECONDS: int = 15 * 60 - 10
    PHONE_KEY_VALUE_AUTHENTICATION_RESET_PASSWORD_TOKEN_LENGTH: int = 4
    PHONE_KEY_VALUE_AUTHENTICATION_RESET_PASSWORD_TOKEN_DOMAIN: str = '1234567890'
    PHONE_KEY_VALUE_AUTHENTICATION_RESET_PASSWORD_SMS_TEMPLATE: str = None

    # Phone OTP
    POA_VERIFICATION_CODE_LENGTH = 4
    POA_VERIFICATION_VALID_SECONDS = 10 * 60
    POA_VERIFICATION_GAP_SECONDS = 60

    # Faker
    FAKER_LOCALE: str = 'fa_IR'
    FAKER_SEED: int = None

    #  Firebase
    FIREBASE_SERVER_TOKEN: Union[str, dict] = ''

    # VisitorToken
    VISITOR_KEY_LENGTH = 40

    # open api
    REQUEST_COMMON_URL_PARAMETERS = [{
        "name": 'language',
        "in": 'query',
        "description": 'set language for this request',
        "required": False,
    }]

    # Neshan
    NESHAN_API_KEY: str = None

    # Chayi
    CHAYI_PROJECT_PACKAGE: str = None
    CHAYI_MODEL_FILE_IMPORTS: str = None

    # Openapi
    OPENAPI_APPLICATION_TITLE = 'NOT_SET'
    OPENAPI_APPLICATION_DESCRIPTION = 'NOT_SET'
    OPENAPI_APPLICATION_VERSION = 'NOT_SET'
    """List of OpenApi.Server"""
    OPENAPI_APPLICATION_SERVERS: list = []

    @classmethod
    def on_startup(cls):
        """
        This method will be called anytime server starts. But just the method from get_avishan_config() result.
        """

        """Run Descriptor to find any error in startup"""
        from avishan.models import AvishanModel
        for model in AvishanModel.get_models():
            model: AvishanModel
            model.direct_callable_methods()

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

    @classmethod
    def get_openapi_schema_models(cls):
        from avishan.models import AvishanModel
        from avishan.descriptor import DjangoAvishanModel
        return [DjangoAvishanModel(target=item) for item in AvishanModel.get_non_abstract_models()]

    @classmethod
    def get_openapi_ignored_path_models(cls) -> List[str]:
        return ['Activity', 'BaseUser', 'UserUserGroup', 'RequestTrackException', 'RequestTrack',
                'TranslatableChar', 'AuthenticationVerification']

    @classmethod
    def email_key_value_authentication_verification_subject(cls, target=None):
        return 'Email Verification'

    @classmethod
    def email_key_value_authentication_verification_body(cls, target=None):
        return 'Your code is {code}'

    @classmethod
    def email_key_value_authentication_verification_html_body(cls, target=None):
        return None

    @classmethod
    def phone_key_value_authentication_verification_body(cls, target=None):
        return 'Your code is {code}'

    @classmethod
    def email_otp_authentication_verification_subject(cls, target=None):
        return 'Email Verification'

    @classmethod
    def email_otp_authentication_verification_body(cls, target=None):
        return 'Your code is {code}'

    @classmethod
    def email_otp_authentication_verification_html_body(cls, target=None):
        return None

    @classmethod
    def phone_otp_authentication_verification_body(cls, target=None):
        return 'Your code is {code}'


def get_avishan_config() -> Union[Type[AvishanConfigFather]]:
    for sub_class in AvishanConfigFather.__subclasses__():
        sub_class: Type[AvishanConfigFather]
        return sub_class
    return AvishanConfigFather
