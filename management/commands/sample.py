from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'help'

    def add_arguments(self, parser):
        pass
        # parser.add_argument('name', type=int, help='help') # arg
        # parser.add_argument('--name', type=int, help='help')  # optional arg
        # parser.add_argument('-a', '--admin', action='store_true', help='Create an admin account') # flag
        # parser.add_argument('user_id', nargs='+', type=int, help='User ID') # list of args

    def handle(self, *args, **kwargs):
        pass

    """
    styles: 
    self.style.ERROR
    self.style.NOTICE
    self.style.SUCCESS
    self.style.WARNING
    
    message = self._get_input_message(field)
    input_value = self.get_input_data(field, message)
    
    """
