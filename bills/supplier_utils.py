import datetime

from django.db.models import Sum
from ledger.models import SupplierLedger
from payments.models import SupplierPayment
from .models import SupplierBill, SupplierBillDetail
from ledger.utils import create_supplier_bill_ledger

def done_drafted_bill(request, bill_obj):
    now = datetime.datetime.now()

    billed_amount = 0
    cash_amount = 0
    total_amount = 0
    total_expense = 0
    total_item_count = 0
    billdetail_vs = list(bill_obj.supplierbilldetail_set.values("rate", "item_count", "unit", "weight", "item_count"))
    for detail_obj in billdetail_vs:
        total_item_count += detail_obj["item_count"]
        if detail_obj["unit"] == 'k':
            total_amount += detail_obj["rate"] * detail_obj["weight"]
        else:
            total_amount += detail_obj["rate"] * detail_obj["item_count"]

    bill_obj.is_draft = False
    if "commission_amount" in bill_obj.other_expence:
        total_expense += percentage(bill_obj.other_expence["commission_amount"], total_amount)
    if "unloading_cost" in bill_obj.other_expence:
        total_expense += float(bill_obj.other_expence["unloading_cost"])*total_item_count
    if "vahicle_rent" in bill_obj.other_expence:
        total_expense += float(bill_obj.other_expence["vahicle_rent"])
    if "farmer_wages" in bill_obj.other_expence:
        total_expense += float(bill_obj.other_expence["farmer_wages"])
    if "labour_cost" in bill_obj.other_expence:
        total_expense += float(bill_obj.other_expence["labour_cost"])
    if "begs_amount" in bill_obj.other_expence:
        total_expense += float(bill_obj.other_expence["begs_amount"])
    if "market_tax" in bill_obj.other_expence:
        total_expense += float(bill_obj.other_expence["market_tax"])
    if "beg_rope" in bill_obj.other_expence:
        total_expense += float(bill_obj.other_expence["beg_rope"])
    if "cash_amount" in bill_obj.other_expence:
        cash_amount = float(bill_obj.other_expence["cash_amount"])

    billed_amount = total_amount - total_expense - cash_amount

    bill_obj.created_time = now
    bill_obj.billed_amount = billed_amount

    if bill_obj.other_expence.get("is_cash", "") == 'n':
        create_supplier_bill_ledger(bill_obj, bill_obj.supplier.current_balance)
        bill_obj.supplier.current_balance += billed_amount
        bill_obj.supplier.save()

    bill_obj.balance = bill_obj.supplier.current_balance
    bill_obj.save()

def get_print_bill_data(request, bill_obj):
    context = {}
    bill_obj.previous_balance = bill_obj.balance - bill_obj.billed_amount
    bill_obj.after_bill_balance = bill_obj.previous_balance + bill_obj.billed_amount

    context["obj"] = bill_obj
    qs = bill_obj.supplierbilldetail_set.all()
    vs = list(qs.values("item__name", "unit", "rate", "weight", "item_count"))
    data = []
    total_amount = 0
    total_expense = 0
    total_item_count = 0
    total_item_weight = 0
    for row in vs:
        detail_obj = {}
        detail_obj["name"] = row["item__name"]
        detail_obj["rate"] = row["rate"]
        detail_obj["item_count"] = row["item_count"]
        detail_obj["unit"] = row["unit"]
        detail_obj["weight"] = row["weight"]
        if row["unit"] == 'k':
            detail_obj["amount"] = round(row["rate"] * row["weight"], 2)
            total_item_weight += row["weight"]
            total_item_count += row["item_count"]
        else:
            detail_obj["amount"] = round(row["rate"] * row["item_count"], 2)
            total_item_count += row["item_count"]

        total_amount += detail_obj["amount"]
        data.append(detail_obj)

    cash_amount = 0
    unloading_cost = 0
    commission_amount = 0
    if "commission_amount" in bill_obj.other_expence:
        commission_amount = percentage(bill_obj.other_expence["commission_amount"], total_amount)
        total_expense += commission_amount
    if "unloading_cost" in bill_obj.other_expence:
        unloading_cost = float(bill_obj.other_expence["unloading_cost"])*total_item_count
        total_expense += unloading_cost
    if "vahicle_rent" in bill_obj.other_expence:
        total_expense += float(bill_obj.other_expence["vahicle_rent"])
    if "farmer_wages" in bill_obj.other_expence:
        total_expense += float(bill_obj.other_expence["farmer_wages"])
    if "labour_cost" in bill_obj.other_expence:
        total_expense += float(bill_obj.other_expence["labour_cost"])
    if "begs_amount" in bill_obj.other_expence:
        total_expense += float(bill_obj.other_expence["begs_amount"])
    if "market_tax" in bill_obj.other_expence:
        total_expense += float(bill_obj.other_expence["market_tax"])
    if "beg_rope" in bill_obj.other_expence:
        total_expense += float(bill_obj.other_expence["beg_rope"])
    if "cash_amount" in bill_obj.other_expence:
        cash_amount = float(bill_obj.other_expence["cash_amount"])

    context["cash_amount"] = round(cash_amount, 2)
    context["commission_amount"] = round(commission_amount, 2)
    context["unloading_cost"] = round(unloading_cost, 2)
    context["bill_detail_list"] = data
    context["total_amount"] = round(total_amount, 2)
    context["total_expense"] = round(total_expense, 2)
    context["total_item_count"] = round(total_item_count, 2)
    context["total_item_weight"] = round(total_item_weight, 2)
    context["final_amount"] = round(total_amount - total_expense, 2)
    context["remaining_amount"] = round(total_amount - total_expense - cash_amount, 2)
    context["is_cash"] = bill_obj.other_expence.get("is_cash")
    context["bill"] = bill_obj
    context["supplier"] = bill_obj.supplier
    context["logo_path"] = request.shop.logo.url

    return context

def get_bill_data(request, supplier_obj, date):
    data = []
    context = {}

    bill_obj = None
    paid_amount = 0
    billed_amount = 0
    total_item_count = 0
    total_item_weight = 0
    calculated_payment_ids = []

    qs = supplierbilldetail.objects.filter(bill__supplier=supplier_obj, bill__bill_date=date, bill__is_draft=False).order_by('id')
    vs = list(qs.values("item__name", "unit", "rate", "weight", "item_count"))
    for row in vs:
        detail_obj = {}
        detail_obj["weight"] = row["weight"]
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

    qs = SupplierLedger.objects.filter(supplier=supplier_obj, tx_date=date).order_by('id')
    vs = list(qs.values('tx_id', 'balance', 'bill_amount', 'payment_amount'))

    bill_obj = SupplierBill(supplier=supplier_obj)
    bill_obj.bill_date = date
    bill_obj.previous_balance = 0
    for i, v in enumerate(vs):
        if i == 0:
            if v['tx_id'].startswith('bill'):
                bill_obj.previous_balance = v['balance'] - v['bill_amount']
            else:
                bill_obj.previous_balance = v['balance'] + v['payment_amount']

        billed_amount += v['bill_amount']
        paid_amount += v['payment_amount']
    if len(vs)>0:
        bill_obj.balance = vs[-1]['balance']
    bill_obj.payment = SupplierPayment(amount=paid_amount)
    bill_obj.after_bill_balance = bill_obj.previous_balance + billed_amount
    bill_obj.billed_amount = billed_amount

    context["obj"] = bill_obj
    context["bill_detail_list"] = data
    context["total_item_count"] = total_item_count
    context["total_item_weight"] = total_item_weight

    return context

def percentage(part, whole):
  return (float(part) / 100 )* float(whole)


def get_supplier_detail(request, context, is_reverse=False):
    obj = context["object"]

    columns = ["id", "supplier__id", "supplier__name", "tx_id", "tx_time", "tx_date",
               "balance", "bill_amount", "payment_amount", "description"]

    qs = obj.supplierledger_set.all()
    today = datetime.date.today()
    start_date = request.GET.get("start_date", "")
    detail_duration = ""
    if bool(start_date):
        start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
        qs = qs.filter(tx_date__gte=start_date)
        start_date = start_date.strftime("%Y-%m-%d")

    end_date = request.GET.get("end_date", "")
    if bool(end_date):
        end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
        qs = qs.filter(tx_date__lte=end_date)
        end_date = end_date.strftime("%Y-%m-%d")

    if bool(start_date) and bool(end_date):
        if start_date == end_date:
            detail_duration = start_date
        else:
            detail_duration = "From %s to %s" % (start_date, end_date)
    elif not bool(end_date):
        detail_duration = "From %s till now" % start_date
    elif not bool(start_date):
        detail_duration = "From start till %s" % end_date
    else:
        detail_duration = "From start till now"

    if is_reverse:
        qs = qs.order_by("-id")
    else:
        qs = qs.order_by("id")
    vs = list(qs.values(*columns))

    data = []
    page_data = []
    total_payment = 0
    opening_balance = 0
    current_balance = 0
    total_billed_amount = 0

    for row in vs:
        row["balance"] = round(row["balance"], 2)
        row["payment_amount"] = round(row["payment_amount"], 2)
        row["bill_amount"] = round(row["bill_amount"], 2)
        row["balance"] = round(row["balance"], 2)
        row["supplier"] = {"id": row.pop("supplier__id"), "name": row.pop("supplier__name")}
        row["normalized_balance"] = "(%s)" % str(row["balance"]*-1) if row["balance"] < 0 else row["balance"]
        page_data.append(row)
        if len(data) == 0 and len(page_data) == 18:
            data.append(page_data)
            page_data = []
        elif len(data) > 0 and len(page_data) == 26:
            data.append(page_data)
            page_data = []

        total_payment += row["payment_amount"]
        total_billed_amount += row["bill_amount"]

    if len(page_data) > 0:
        data.append(page_data)

    if len(data) > 0:
        if data[0][0]["payment_amount"]:
            opening_balance = "(%s)" % round(data[0][0]["payment_amount"], 2)
        else:
            opening_balance = round(data[0][0]["bill_amount"], 2)

        current_balance = round(data[-1][-1]["balance"], 2)

    context["data"] = data
    context["start_date"] = start_date
    context["end_date"] = end_date
    context["total_payment"] = round(total_payment, 2)
    context["total_billed_amount"] = round(total_billed_amount, 2)
    context["opening_balance"] = opening_balance
    context["current_balance_str"] = "(%s)" % str(current_balance*-1) if current_balance < 0 else str(current_balance)
    context["current_balance"] = current_balance
    context["detail_duration"] = detail_duration

    return context

def get_supplier_daily_detail(request, context):
    columns = ["id", "supplier__id", "cash", "supplier__identifier", "supplier__name", "other_expence"]
    qs = context["object_list"]

    today = datetime.date.today()
    start_date = request.GET.get("start_date", "")
    detail_duration = ""
    if bool(start_date):
        start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
    else:
        start_date = today
    qs = qs.filter(bill_date__gte=start_date)
    start_date = start_date.strftime("%Y-%m-%d")

    end_date = request.GET.get("end_date", "")
    if bool(end_date):
        end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
    else:
        end_date = today
        
    qs = qs.filter(bill_date__lte=end_date)
    end_date = end_date.strftime("%Y-%m-%d")

    if bool(start_date) and bool(end_date):
        if start_date == end_date:
            detail_duration = start_date
        else:
            detail_duration = "From %s to %s" % (start_date, end_date)
    elif not bool(end_date):
        detail_duration = "From %s till now" % start_date
    elif not bool(start_date):
        detail_duration = "From start till %s" % end_date
    else:
        detail_duration = "From start till now"

    qs = qs.filter(supplier__shop=request.shop, is_draft=False).order_by("supplier__identifier")
    vs = list(qs.values(*columns))

    data = {}
    page_data = []
    cumulative_cash = 0
    cumulative_expense = 0
    cumulative_billed_amount = 0
    cumulative_commission_amount = 0
    cumulative_unloading_cost = 0
    cumulative_actual_billed_amount = 0

    for row in vs:
        supplier_id = row.pop("supplier__id")
        row["supplier"] = {"id": supplier_id, "identifier": row.pop("supplier__identifier"), "name": row.pop("supplier__name")}

        total_item_count = 0
        actual_billed_amount = 0
        qs = SupplierBillDetail.objects.filter(bill=row["id"])
        vs = list(qs.values("unit", "weight", "rate", "item_count"))
        for detail_obj in vs:

            if detail_obj["unit"] == 'k':
                actual_billed_amount += detail_obj["rate"] * detail_obj["weight"]
            else:
                actual_billed_amount += detail_obj["rate"] * detail_obj["item_count"]

            total_item_count += detail_obj["item_count"]

        other_expence = row["other_expence"]
        if "commission_amount" in other_expence:
            commission_amount = percentage(other_expence["commission_amount"], actual_billed_amount)
        if "unloading_cost" in other_expence:
            unloading_cost = float(other_expence["unloading_cost"])*total_item_count

        row["commission_amount"] = round(commission_amount, 2)
        row["unloading_cost"] = round(unloading_cost, 2)
        row["actual_billed_amount"] = round(actual_billed_amount, 2)

        total_expense = 0
        if "vahicle_rent" in other_expence:
            total_expense += float(other_expence["vahicle_rent"])
        if "farmer_wages" in other_expence:
            total_expense += float(other_expence["farmer_wages"])
        if "labour_cost" in other_expence:
            total_expense += float(other_expence["labour_cost"])
        if "begs_amount" in other_expence:
            total_expense += float(other_expence["begs_amount"])
        if "market_tax" in other_expence:
            total_expense += float(other_expence["market_tax"])
        if "beg_rope" in other_expence:
            total_expense += float(other_expence["beg_rope"])
        if "cash_amount" in other_expence:
           total_expense += float(other_expence["cash_amount"])

        is_cash = other_expence.get("is_cash")
        if is_cash == 'n':
            row["total_expense"] = total_expense
            row["billed_amount"] = actual_billed_amount - (commission_amount + unloading_cost + total_expense)
        else:
            row["total_expense"] = actual_billed_amount - (commission_amount + unloading_cost)
            row["billed_amount"] = 0

        if supplier_id in data:
            data[supplier_id]["commission_amount"] = round(data[supplier_id]["commission_amount"] + row["commission_amount"], 2)
            data[supplier_id]["unloading_cost"] = round(data[supplier_id]["unloading_cost"] + row["unloading_cost"], 2)
            data[supplier_id]["actual_billed_amount"] = round(data[supplier_id]["actual_billed_amount"] + row["actual_billed_amount"], 2)
            data[supplier_id]["total_expense"] = round(data[supplier_id]["total_expense"] + row["total_expense"], 2)
            data[supplier_id]["billed_amount"] = round(data[supplier_id]["billed_amount"] + row["billed_amount"], 2)
            data[supplier_id]["cash"] += round(row["cash"], 2)
        else:
            row["commission_amount"] = round(row["commission_amount"], 2)
            row["unloading_cost"] = round(row["unloading_cost"], 2)
            row["actual_billed_amount"] = round(row["actual_billed_amount"], 2)
            row["total_expense"] = round(row["total_expense"], 2)
            row["billed_amount"] = round(row["billed_amount"], 2)
            row["cash"] = round(row["cash"], 2)
            data[supplier_id] = row

        cumulative_expense += row["total_expense"]
        cumulative_billed_amount += row["billed_amount"]
        cumulative_commission_amount += row["commission_amount"]
        cumulative_unloading_cost += row["unloading_cost"]
        cumulative_actual_billed_amount += row["actual_billed_amount"]
        cumulative_cash += row["cash"]

    row = {}
    row["total_expense"] = round(cumulative_expense, 2)
    row["billed_amount"] = round(cumulative_billed_amount, 2)
    row["commission_amount"] = round(cumulative_commission_amount, 2)
    row["unloading_cost"] = round(cumulative_unloading_cost, 2)
    row["actual_billed_amount"] = round(cumulative_actual_billed_amount, 2)
    row["cash"] = round(cumulative_cash, 2)
    row["supplier"] = {"name": "Total"}

    data[0] = row
    context["data"] = [data.values()]
    context["detail_duration"] = detail_duration
    context["start_date"] = start_date
    context["end_date"] = end_date
    return context
