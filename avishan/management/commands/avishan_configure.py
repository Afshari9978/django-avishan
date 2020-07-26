from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Creates avishan config file'

    def handle(self, *args, **kwargs):
        from avishan.configure import AvishanConfigure

        AvishanConfigure.command_line_checkup(self)
