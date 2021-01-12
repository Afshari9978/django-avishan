from datetime import timedelta

from django.utils import timezone

from avishan.models import RequestTrack
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Cleans RequestTrack objects'

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=int,
            help='1: last day & exception-added | 2: last day | 3: exception-added | 4: all',
        )

    def handle(self, *args, **kwargs):
        delete_type = kwargs['type']
        if not delete_type:
            delete_type = 1

        deletes = RequestTrack.objects.all()
        if delete_type in [1, 2]:
            now = timezone.now()
            deletes = deletes.filter(start_time__lte=now - timedelta(days=1))

        if delete_type in [1, 3]:
            deletes = deletes.filter(exception__isnull=True)

        deletes.delete()
