import datetime

from clients.models import Client
from payments.models import ClientPayment
from bills.models import ClientBill

from .models import *


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
    for obj in list(bill_obj.billdetail_set.all()):
        s = "%s[%.2f][%.2f]" % (obj.item.name, obj.item_count, obj.rate)
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

def update_ledger_date(tx_id, tx_date, description=""):
    try:
        ledger = ClientLedger.objects.get(tx_id=tx_id)
        ledger.tx_date = tx_date
        if len(description) > 0:
            ledger.description = description
        ledger.save()
    except ClientLedger.DoesNotExist:
        pass

def delete_ledger(tx_id):
    try:
        ledger = ClientLedger.objects.get(tx_id=tx_id)
        ledger.delete()
    except ClientLedger.DoesNotExist:
        pass

def create_supplier_opening_ledger(supplier_obj):
    ledger = SupplierLedger()
    ledger.supplier = supplier_obj
    ledger.tx_id = "supplier-%d" % supplier_obj.id
    ledger.tx_time = supplier_obj.created_time
    ledger.tx_date = supplier_obj.created_time.date()
    if supplier_obj.opening_balance > 0:
        ledger.bill_amount = supplier_obj.opening_balance
    elif supplier_obj.opening_balance < 0:
        ledger.payment_amount = supplier_obj.opening_balance * -1
    ledger.balance = supplier_obj.opening_balance
    ledger.description = "Opening Blance"
    ledger.save()
    return ledger

def create_supplier_bill_ledger(bill_obj, balance):
    ledger = SupplierLedger()
    ledger.supplier = bill_obj.supplier
    ledger.tx_id = "bill-%d" % bill_obj.pk
    ledger.tx_time = bill_obj.created_time
    ledger.tx_date = bill_obj.bill_date
    ledger.bill_amount = bill_obj.billed_amount
    ledger.balance = balance + bill_obj.billed_amount
    description = []
    for obj in list(bill_obj.supplierbilldetail_set.all()):
        if obj.weight and obj.weight > 0:
            s = "%s[%.2f][%.2f][%.2f]" % (obj.item.name, obj.item_count, obj.weight, obj.rate)
        else:
            s = "%s[%.2f][%.2f]" % (obj.item.name, obj.item_count, obj.rate)
        description.append(s)
    ledger.description = ", ".join(description)
    ledger.save()
    return ledger

def create_supplier_payment_ledger(payment_obj, balance):
    ledger = SupplierLedger()
    ledger.supplier = payment_obj.supplier
    ledger.tx_id = "payment-%d" % payment_obj.pk
    ledger.tx_time = payment_obj.payment_time
    ledger.tx_date = payment_obj.payment_date

    if payment_obj.payment_type == "i":
        ledger.bill_amount = payment_obj.amount
    else:
        ledger.payment_amount = payment_obj.amount

    ledger.balance = balance
    ledger.description = payment_obj.description
    ledger.save()
    return ledger

def update_supplier_ledger_date(tx_id, tx_date, description=""):
    try:
        ledger = SupplierLedger.objects.get(tx_id=tx_id)
        ledger.tx_date = tx_date
        if len(description) > 0:
            ledger.description = description
        ledger.save()
    except SupplierLedger.DoesNotExist:
        pass

def delete_supplier_ledger(tx_id):
    try:
        ledger = SupplierLedger.objects.get(tx_id=tx_id)
        ledger.delete()
    except SupplierLedger.DoesNotExist:
        pass

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
