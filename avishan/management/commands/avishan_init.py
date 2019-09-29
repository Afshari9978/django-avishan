from importlib import import_module

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Avishan init'

    def handle(self, *args, **kwargs):
        """ todo check ha
         use tz
         static
         media
        """
        # todo create avishan_config file on project root
        init_file = import_module('avishan.init')
        init_file.init()
        self.stdout.write(self.style.SUCCESS('init function executed successfully'))
