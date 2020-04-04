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
    ledger.description = "Billed against item %s " % ", ".join(description)
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
