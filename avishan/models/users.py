from avishan.models import *
from avishan.third_party_packages.kavenegar import KavenegarSMS


class UserGroup(AvishanModel):
    title = models.CharField(max_length=255, unique=True)
    can_sign_in_using_email_password = models.BooleanField(default=False)
    can_sign_up_using_email_password = models.BooleanField(default=False)

    def __str__(self):
        return self.title


class User(AvishanModel):
    first_name = models.CharField(max_length=255, blank=True)
    last_name = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=False)

    compact_fields = ('first_name', 'last_name')
    list_display = ('__str__', 'is_active')
    private_fields = ['id']

    def __str__(self):
        try:
            if self.first_name or self.last_name:
                return self.first_name + " " + self.last_name
        except:
            return super().__str__()

    # todo show user id for django admin better filter

    def token_authenticate(self):
        pass
        # todo check user
        # todo add token to response

    def add_to_user_group(self, user_group: UserGroup):
        try:
            UserUserGroup.get(
                avishan_raise_exception=True,
                user=self,
                user_group=user_group
            )
        except UserUserGroup.DoesNotExist:
            UserUserGroup.create(
                user=self,
                user_group=user_group,
            )


class UserUserGroup(AvishanModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_user_groups')
    user_group = models.ForeignKey(UserGroup, on_delete=models.CASCADE, related_name='user_user_groups')
    date_last_used = models.DateTimeField(blank=True, null=True)

    list_display = ('user', 'user_group', 'date_last_used')

    def __str__(self):
        return str(self.user) + ' - ' + str(self.user_group)
