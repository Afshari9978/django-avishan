import bcrypt

from avishan.models import *
from avishan.models.users import UserUserGroup, UserGroup
from avishan.third_party_packages.kavenegar import KavenegarSMS


class UserAuthType(AvishanModel):
    is_logged_in = models.BooleanField(default=False)
    date_last_sign_in = models.DateTimeField(blank=True, null=True)
    date_last_sign_out = models.DateTimeField(blank=True, null=True)

    # note: every user auth type must have user_user_group
    # user_user_group = models.OneToOneField(UserUserGroup, on_delete=models.CASCADE)

    class Meta:
        abstract = True

    def sign_in(self, **kwargs):
        self.is_logged_in = True
        self.date_last_sign_in = BchDatetime().to_datetime()
        self.save()
        self.user_user_group.user.token_authenticate()

    @classmethod
    def sign_up(cls, **kwargs):
        # todo
        cls.sign_in()

    def sign_out(self):
        self.date_last_sign_out = BchDatetime().to_datetime()
        self.save()

    @staticmethod
    def hash_password(password):
        return bcrypt.hashpw(password.encode('utf8'), bcrypt.gensalt()).decode('utf8')

    @staticmethod
    def check_password(entered, source):
        return bcrypt.checkpw(bytes(entered, 'utf-8'), bytes(source, 'utf-8'))


class UserAuthEmailPassword(UserAuthType):
    user_user_group = models.OneToOneField(UserUserGroup, on_delete=models.CASCADE,
                                           related_name='user_auth_email_password')

    email = models.CharField(max_length=255)  # todo unique for usergroup
    password = models.CharField(max_length=255, blank=True)

    list_display = ('user_user_group', 'email')

    @staticmethod
    def sign_in(email: str, password: str):
        try:
            self = UserAuthEmailPassword.get(email=email, avishan_raise_exception=True)
        except UserAuthEmailPassword.DoesNotExist:
            from avishan.exceptions import AuthException
            raise AuthException(AuthException.ACCOUNT_NOT_FOUND)
        # todo
        super().sign_in()


class ActivationCode(AvishanModel):
    code = models.CharField(max_length=255)
    user_group = models.ForeignKey(UserGroup, on_delete=models.CASCADE, null=True, blank=True)
    kavenegar_sms = models.ForeignKey(KavenegarSMS, on_delete=models.CASCADE)

    list_display = ('kavenegar_sms', 'code')

    def __str__(self):
        return self.kavenegar_sms.receptor + ' - ' + self.code
