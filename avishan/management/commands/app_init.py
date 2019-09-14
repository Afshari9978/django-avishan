from django.core.management.base import BaseCommand


# todo: these arent init. these are configs
# todo: create some functions to help writing configs like have_model & other
class Command(BaseCommand):
    help = 'Execute init commands from <app>/inti.py init function'

    def add_arguments(self, parser):
        parser.add_argument('app_name', type=str, help='app name')

    def handle(self, *args, **kwargs):
        from importlib import import_module
        app_name = kwargs['app_name']
        try:
            import_module(app_name)
        except ModuleNotFoundError:
            self.stdout.write(self.style.ERROR('%s package not found' % app_name))
            return
        try:
            init_file = import_module(app_name + ".init")
        except ModuleNotFoundError:
            self.stdout.write(self.style.ERROR('%s/init.py file not found' % app_name))
            return
        try:
            init_file.init()
            self.stdout.write(self.style.SUCCESS('init function executed successfully'))
        except AttributeError as e:
            self.stdout.write(self.style.ERROR(e.args))
            self.stdout.write(self.style.ERROR('init function not located in %s/init.py' % app_name))

