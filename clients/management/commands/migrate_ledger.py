from django.core.management.base import BaseCommand

from clients.models import Client
from ledger.utils import migrate_client_ledger


class Command(BaseCommand):
    help = 'Command to migrate ledger'

    def add_arguments(self, parser):
        # Optional argument
        parser.add_argument('-c', '--client', type=int, help='Enter a client id to migrate ledger', )

    def handle(self, *args, **kwargs):

        if (kwargs.get('client') or 0) > 0:
            qs = Client.objects.filter(id=kwargs.get('client'))
        else:
            qs = Client.objects.all()
        self.stdout.write("Going to migrate %d clients" % qs.count())

        for client_obj in qs:
            self.stdout.write("Going to migrate client ID: %d" % client_obj.id)
            migrate_client_ledger(client_obj)
