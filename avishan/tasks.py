from logging import Logger

from celery import shared_task

from avishan.models import PhoneOtpAuthenticate
from celery.utils.log import get_task_logger

logger: Logger = get_task_logger(__name__)


@shared_task(name='avishan.async_phone_otp_authentication_send_otp_code')
def async_phone_otp_authentication_send_otp_code(poa_id: int):
    try:
        PhoneOtpAuthenticate.get(id=poa_id).send_otp_code()
    except PhoneOtpAuthenticate.DoesNotExist:
        logger.error(f'poa {poa_id} not found')
