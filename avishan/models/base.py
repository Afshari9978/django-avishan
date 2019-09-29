from avishan.models import *
from avishan.models.users import User, UserGroup


class Image(AvishanModel):
    file = models.ImageField(blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    private_fields = ('date_created',)
    list_display = ('__str__', 'user', 'date_created')

    def __str__(self):
        return self.file.name

    def to_dict(self, **kwargs) -> dict:
        temp = {}
        temp['url'] = self.file.url
        temp['id'] = self.id
        return temp
    # todo: override delete() to fully remove from hard disk
    # todo: override create to chmod
    # todo: override create with compression util


class File(AvishanModel):
    file = models.FileField(blank=True)
    private_fields = ('date_created',)
    list_display = ('file', 'date_created')

    def __str__(self):
        return self.file.name


class ExceptionRecord(AvishanModel):
    class_title = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    user_group = models.ForeignKey(UserGroup, on_delete=models.SET_NULL, null=True, blank=True)
    status_code = models.IntegerField()
    request_url = models.TextField()
    request_method = models.CharField(max_length=255)
    request_data = models.TextField()
    request_headers = models.TextField(null=True)
    response = models.TextField()
    traceback = models.TextField()
    exception_args = models.TextField(null=True)
    checked = models.BooleanField(default=False)

    list_display = ('class_title', 'date_created', 'get_title', 'user', 'checked')
    list_filter = ('class_title', 'user', 'request_url', 'checked')
    date_hierarchy = 'date_created'

    # todo remove user from filter and add search
    @property
    def get_title(self):
        # try:
        if self.exception_args:
            return self.exception_args
        return self.response
    # except:
    #     return 'UNKNOWN'
# todo: create a request copy model. to keep request full data
