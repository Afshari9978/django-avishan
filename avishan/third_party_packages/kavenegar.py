from avishan.models import *


class KavenegarSMS(AvishanModel):
    STATUS_TYPES = {
        'in_queue': 1,
        'scheduled': 2,
        'sent_to_telecom': 4,
        'sent_to_telecom2': 5,
        'failed': 6,
        'delivered': 10,
        'undelivered': 11,
        'user_canceled_sms': 13,
        'user_blocked_sms': 14,
        'invalid_id': 100
    }
    receptor = models.CharField(max_length=255)
    message = models.TextField()
    template_title = models.CharField(max_length=255, null=True, blank=True)

    http_status_code = models.CharField(max_length=255,
                                        blank=True)  # todo: https://kavenegar.com/rest.html#result-general
    message_id = models.CharField(max_length=255, blank=True)
    status = models.IntegerField(default=-1, blank=True)
    sender = models.CharField(max_length=255, blank=True)
    date = models.DateTimeField(blank=True, null=True)
    cost = models.IntegerField(blank=True, default=0)

    list_display = ('receptor', 'message', 'template_title', 'http_status_code', 'status', 'cost')

    def __str__(self):
        return self.receptor

    @classmethod
    def class_plural_snake_case_name(cls) -> str:
        return 'kavenegar_smses'

    # todo add user field blank=True
