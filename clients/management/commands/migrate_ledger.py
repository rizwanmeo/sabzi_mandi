from django.core.management.base import BaseCommand
from django.utils import timezone

from clients.models import Client
from payments.models import ClientPayment
from client_bills.models import ClientBill

from ledger.utils import *
from ledger.models import ClientLedger

class Command(BaseCommand):
    help = 'Command to migrate ledger'

    def handle(self, *args, **kwargs):
        time = timezone.now().strftime('%X')

        qs = Client.objects.all()
        self.stdout.write("Going to migrate %d clients" % qs.count())

        for client_obj in qs:
            self.stdout.write("Going to migrate client ID: %d" % client_obj.id)
            # Client opening balance detail
            data = []

            row = {}
            row["tx_time"] = client_obj.created_time
            row["obj"] = client_obj
            data.append(row)

            # Client bill detail
            qs = list(client_obj.clientbill_set.all())
            for bill_obj in qs:
                if bill_obj.payment and bill_obj.is_draft:
                    bill_obj.payment.delete()
                    continue

                row = {}
                row["tx_time"] = bill_obj.created_time
                row["obj"] = bill_obj
                data.append(row)

            # Client payment detail
            qs = list(client_obj.clientpayment_set.all())
            for payment_obj in qs:
                row = {}
                row["tx_time"] = payment_obj.payment_time
                row["obj"] = payment_obj
                data.append(row)

            data = sorted(data, key = lambda i: i['tx_time'])
            ClientLedger.objects.filter(client=client_obj).delete()
            balance = 0
            for row in data:
                obj = row["obj"]
                if isinstance(obj, Client):
                    ledger = create_opening_ledger(obj)
                    balance = ledger.balance
                elif isinstance(obj, ClientBill):
                    ledger = create_bill_ledger(obj, balance)
                    balance = ledger.balance
                elif isinstance(obj, ClientPayment):
                    ledger = create_payment_ledger(obj, balance)
                    balance = ledger.balance
