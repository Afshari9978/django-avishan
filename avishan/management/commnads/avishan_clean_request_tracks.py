from django.core.management.base import BaseCommand

from avishan.models import RequestTrack


class Command(BaseCommand):
    help = 'Creates avishan config file'

    def handle(self, *args, **kwargs):
        counter = 0
        for item in RequestTrack.objects.all():
            item.remove()
            counter += 1
            if counter % 100 == 0:
                self.stdout.write(self.style.SUCCESS(f'clean {counter} items...'))
        self.stdout.write(self.style.SUCCESS(f'clean all {counter} items.'))

