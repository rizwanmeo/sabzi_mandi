import datetime

from django.db.models import Sum
from clients.models import Client
from payments.models import ClientPayment
from ledger.utils import create_bill_ledger, create_payment_ledger


def done_drafted_bill(request, bill_obj):
    billed_amount = 0
    now = datetime.datetime.now()
    billdetail_vs = list(bill_obj.billdetail_set.values("rate", "item_count"))
    for detail_obj in billdetail_vs:
        billed_amount += detail_obj["rate"] * detail_obj["item_count"]
    bill_obj.is_draft = False
    bill_obj.billed_amount = billed_amount

    bill_obj.created_time = now
    create_bill_ledger(bill_obj, bill_obj.client.current_balance)
    bill_obj.client.current_balance += billed_amount

    if bill_obj.payment:
        bill_obj.payment.payment_time = now + datetime.timedelta(seconds=1)
        bill_obj.payment.is_draft = False
        description = "Payment received against bill ID bill-%d" % bill_obj.id
        bill_obj.payment.description = description
        create_payment_ledger(bill_obj.payment, bill_obj.client.current_balance)
        bill_obj.client.current_balance -= bill_obj.payment.amount
        bill_obj.payment.save()

    bill_obj.balance = bill_obj.client.current_balance
    bill_obj.client.save()
    bill_obj.save()

def get_print_bill_data(request, bill_obj):
    context = {}
    if bill_obj.payment:
        bill_obj.previous_balance = bill_obj.balance - bill_obj.billed_amount + bill_obj.payment.amount
    else:
        bill_obj.previous_balance = bill_obj.balance - bill_obj.billed_amount
    bill_obj.after_bill_balance = bill_obj.previous_balance + bill_obj.billed_amount

    context["obj"] = bill_obj
    qs = bill_obj.billdetail_set.all()
    vs = list(qs.values("item__name", "unit", "rate", "item_count"))
    data = []
    total_item_count = 0
    total_item_weight = 0
    for row in vs:
        detail_obj = {}
        detail_obj["name"] = row["item__name"]
        detail_obj["rate"] = row["rate"]
        detail_obj["item_count"] = row["item_count"]
        detail_obj["amount"] = row["rate"] * row["item_count"]
        detail_obj["unit"] = row["unit"]
        if row["unit"] == 'k':
            total_item_weight += row["item_count"]
        else:
            total_item_count += row["item_count"]

        data.append(detail_obj)

    context["bill_detail_list"] = data
    context["total_item_count"] = total_item_count
    context["total_item_weight"] = total_item_weight

    return context


def get_bill_data(request, client_obj, date):
    data = []
    context = {}

    bill_obj = None
    paid_amount = 0
    billed_amount = 0
    total_item_count = 0
    total_item_weight = 0
    calculated_payment_ids = []

    bill_qs = list(client_obj.clientbill_set.filter(bill_date=date, is_draft=False).order_by('id'))
    for obj in bill_qs:
        if bill_obj is None:
            bill_obj = obj

        billed_amount += obj.billed_amount
        if obj.payment:
            paid_amount += obj.payment.amount
            calculated_payment_ids.append(obj.payment.id)           

        qs = obj.billdetail_set.all()
        vs = list(qs.values("item__name", "unit", "rate", "item_count"))
        for row in vs:
            detail_obj = {}
            detail_obj["name"] = row["item__name"]
            detail_obj["rate"] = row["rate"]
            detail_obj["item_count"] = row["item_count"]
            detail_obj["amount"] = row["rate"] * row["item_count"]
            detail_obj["unit"] = row["unit"]
            if row["unit"] == 'k':
                total_item_weight += row["item_count"]
            else:
                total_item_count += row["item_count"]

            data.append(detail_obj)

    if len(data) == 0:
        return context

    
    payment_qs = client_obj.clientpayment_set.filter(payment_date=date, is_draft=False)
    if len(calculated_payment_ids) > 0:
        payment_qs = payment_qs.exclude(id__in=calculated_payment_ids)
    payment_vs = payment_qs.aggregate(amount=Sum('amount'))

    bill_obj.previous_balance = bill_obj.balance - bill_obj.billed_amount
    bill_obj.payment = ClientPayment(amount=paid_amount + (payment_vs['amount'] or 0))
    bill_obj.after_bill_balance = bill_obj.previous_balance + billed_amount
    bill_obj.billed_amount = billed_amount

    bill_obj.balance = bill_obj.after_bill_balance - bill_obj.payment.amount

    context["obj"] = bill_obj
    context["bill_detail_list"] = data
    context["total_item_count"] = total_item_count
    context["total_item_weight"] = total_item_weight

    return context

