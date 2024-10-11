from django.db.models import Sum

from .models import *
from sabzi_mandi.views import *

from ledger.models import ClientLedger
from bills.models import SupplierBill, SupplierBillDetail

def percentage(part, whole):
  return (float(part) / 100 )* float(whole)


def get_shop_cashbook_data(request):
    context = {}

    date = request.GET.get("date", "")
    if bool(date):
        date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
    else:
        date = datetime.date.today()

    object_list1 = ShopCashbook.objects.filter(shop=request.shop, time__gte=date, cash_type='i')
    object_list2 = ShopCashbook.objects.filter(shop=request.shop, time__gte=date, cash_type='e')

    income_amount = object_list1.aggregate(total_amount=Sum('amount'))
    income_amount = income_amount.get("total_amount") or 0

    expense_amount = object_list2.aggregate(total_amount=Sum('amount'))
    expense_amount = expense_amount.get("total_amount") or 0

    payment_qs = ClientLedger.objects.filter(client__shop=request.shop, tx_date__gte=date, tx_id__startswith='payment')
    payment_vs = payment_qs.aggregate(total_amount=Sum('payment_amount'))

    cash_amount = 0
    total_expense = 0
    columns = ["id", "cash", "other_expence"]
    supplier_bill_qs = SupplierBill.objects.filter(supplier__shop=request.shop, bill_date__gte=date)
    supplier_bill_vs = list(supplier_bill_qs.values(*columns))
    #supplier_cash_vs = supplier_cash_qs.aggregate(total_amount=Sum('cash'))
    #print("supplier_cash_vs", supplier_cash_vs)

    for row in supplier_bill_vs:
        other_expence = row["other_expence"]

        bill_expense_amount = 0
        unloading_cost = 0
        total_item_count = 0
        commission_amount = 0
        actual_billed_amount = 0

        qs = SupplierBillDetail.objects.filter(bill=row["id"])
        vs = list(qs.values("unit", "weight", "rate", "item_count"))
        for detail_obj in vs:
            if detail_obj["unit"] == 'k':
                actual_billed_amount += detail_obj["rate"] * detail_obj["weight"]
            else:
                actual_billed_amount += detail_obj["rate"] * detail_obj["item_count"]
            total_item_count += detail_obj["item_count"]

        if "commission_amount" in other_expence:
            commission_amount = percentage(other_expence["commission_amount"], actual_billed_amount)
        if "unloading_cost" in other_expence:
            unloading_cost = float(other_expence["unloading_cost"])*total_item_count
        if "vahicle_rent" in other_expence:
            bill_expense_amount += float(other_expence["vahicle_rent"])
        if "farmer_wages" in other_expence:
            bill_expense_amount += float(other_expence["farmer_wages"])
        if "labour_cost" in other_expence:
            bill_expense_amount += float(other_expence["labour_cost"])
        if "begs_amount" in other_expence:
            bill_expense_amount += float(other_expence["begs_amount"])
        if "market_tax" in other_expence:
            bill_expense_amount += float(other_expence["market_tax"])
        if "beg_rope" in other_expence:
            bill_expense_amount += float(other_expence["beg_rope"])
        if "cash_amount" in other_expence:
           bill_expense_amount += float(other_expence["cash_amount"])

        is_cash = other_expence.get("is_cash")
        if is_cash == 'n':
            total_expense += bill_expense_amount
        else:
            cash_amount += row["cash"]
            total_expense += actual_billed_amount - (commission_amount + unloading_cost)

    init_amount = 0
    try:
        obj = ShopDailyRemainingCash.objects.get(shop=request.shop, date__gte=date, date__lte=date)
        init_amount = obj.amount
    except ShopDailyRemainingCash.DoesNotExist:
        pass

    context["logo_path"] = request.shop.logo.url if request.shop.logo else ""
    context["cashbook_date"] = date.strftime("%Y-%m-%d")
    context["object_list1"] = object_list1
    context["object_list2"] = object_list2
    context["payment_amount"] = payment_vs.get("total_amount") or 0
    context["init_amount"] = init_amount
    context["expense_amount"] = total_expense
    context["supplier_cash_amount"] = cash_amount
    context["total_income_amount"] = income_amount + init_amount + cash_amount + context["payment_amount"]
    context["total_expense_amount"] = expense_amount + total_expense
    context["remaining_amount"] = context["total_income_amount"] - context["total_expense_amount"]
    return context
