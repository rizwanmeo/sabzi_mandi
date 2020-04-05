import datetime

from clients.models import Client
from payments.models import ClientPayment
from client_bills.models import ClientBill

from .models import ClientLedger


def create_opening_ledger(client_obj):
    ledger = ClientLedger()
    ledger.client = client_obj
    ledger.tx_id = "client-%d" % client_obj.id
    ledger.tx_time = client_obj.created_time
    ledger.tx_date = client_obj.created_time.date()
    ledger.balance = client_obj.opening_balance
    ledger.description = "Opening Blance"
    ledger.save()
    return ledger

def create_bill_ledger(bill_obj, balance):
    ledger = ClientLedger()
    ledger.client = bill_obj.client
    ledger.tx_id = "bill-%d" % bill_obj.pk
    ledger.tx_time = bill_obj.created_time
    ledger.tx_date = bill_obj.bill_date
    ledger.bill_amount = bill_obj.billed_amount
    ledger.balance = balance + bill_obj.billed_amount
    description = []
    for obj in bill_obj.billdetail_set.all():
        s = "%s[%d][%d]" % (obj.item.name, obj.item_count, obj.rate)
        description.append(s)
    ledger.description = ", ".join(description)
    ledger.save()
    return ledger

def create_payment_ledger(payment_obj, balance):
    ledger = ClientLedger()
    ledger.client = payment_obj.client
    ledger.tx_id = "payment-%d" % payment_obj.pk
    ledger.tx_time = payment_obj.payment_time
    ledger.tx_date = payment_obj.payment_date
    ledger.payment_amount = payment_obj.amount
    ledger.balance = balance - payment_obj.amount
    ledger.description = payment_obj.description
    ledger.save()
    return ledger


def migrate_client_ledger(client_obj):
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
        if bill_obj.created_time < client_obj.created_time:
            row["tx_time"] = client_obj.created_time + datetime.timedelta(minutes=5)
        else:
            row["tx_time"] = bill_obj.created_time
        row["obj"] = bill_obj
        data.append(row)

    # Client payment detail
    qs = list(client_obj.clientpayment_set.all())
    for payment_obj in qs:
        row = {}
        if payment_obj.payment_time < client_obj.created_time:
            row["tx_time"] = client_obj.created_time + datetime.timedelta(minutes=5)
        else:
            row["tx_time"] = payment_obj.payment_time
        row["obj"] = payment_obj
        data.append(row)

    data = sorted(data, key = lambda i: i['tx_time'])
    ClientLedger.objects.filter(client=client_obj).delete()
    balance = 0
    for row in data:
        obj = row["obj"]
        created_time = row["tx_time"]
        if client_obj.created_time > created_time:
            continue

        if isinstance(obj, Client):
            ledger = create_opening_ledger(obj)
            balance = ledger.balance
        elif isinstance(obj, ClientBill):
            ledger = create_bill_ledger(obj, balance)
            balance = ledger.balance
        elif isinstance(obj, ClientPayment):
            ledger = create_payment_ledger(obj, balance)
            balance = ledger.balance
