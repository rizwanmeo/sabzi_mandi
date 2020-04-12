import datetime
from collections import defaultdict

from django.db.models import Q
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django_filters.filterset import filterset_factory
from django.views.decorators.http import require_http_methods

from clients.models import Client
from suppliers.models import Supplier
from ledger.models import ClientLedger
from payments.models import SupplierPayment


def get_suppliers_ledger_data(request):
    data = []
    context = {}
    if request.method == "GET":
        supplier_id = request.GET.get("supplier", "")
        supplier_id=int(supplier_id) if supplier_id.isdigit() else 0
        if supplier_id == 0:
            qs = SupplierPayment.objects.none()
        else:
            qs = SupplierPayment.objects.filter(supplier__shop=request.shop)

        SupplierPaymentFilter = filterset_factory(model=SupplierPayment, fields=["supplier"])
        f = SupplierPaymentFilter(request.GET, queryset=qs)
        columns = ['supplier__name', 'payment_type', 'payment_date', 'description', 'amount']
        vs = list(f.qs.values(*columns))
        for obj in vs:
            row = {}
            row["name"] = obj["supplier__name"]
            row["amount"] = obj["amount"]
            row["pament_type"] = obj["payment_type"]
            row["pament_date"] = obj["payment_time"]
            row["description"] = obj["description"]
            row["remaining_amount"] = ""
            data.append(row)
        context["ledger_list"] = data
        context["selected_supplier"] = supplier_id
    return context

@login_required(login_url='/login/')
def suppliers_ledger_view(request):
    context = get_suppliers_ledger_data(request)

    # Getting all suppliers for filter
    qs = Supplier.objects.filter(shop=request.shop)
    context["supplier_list"] = list(qs.values("id", "name"))

    return render(request, 'ledger/suppliers_ledger_list.html', context)

@login_required(login_url='/login/')
def suppliers_ledger_print(request):
    context = get_suppliers_ledger_data(request)
    return render(request, 'ledger/suppliers_ledger_print.html', context)

def get_client_ledger_data(request):
    data = {}
    context = {}
    total_payment = 0
    total_previous_balance = 0
    total_current_balance = 0
    total_billed_amount = 0

    today = datetime.date.today()
    selected_date = request.GET.get("ledger_date", "")
    if selected_date == "":
        selected_date = today
    else:
        try:
            selected_date = datetime.datetime.strptime(selected_date, "%Y-%m-%d").date()
        except ValueError:
            selected_date = today

    kwargs = {"client__shop": request.shop, "tx_date": selected_date}
    ledger_qs = ClientLedger.objects.filter(**kwargs)
    columns = ["client__id", "client__name", "balance", "payment_amount", "bill_amount"]
    ledger_qs = ledger_qs.order_by("client", "-tx_time")
    ledger_vs = ledger_qs.values(*columns)

    tmp_data = defaultdict(list)
    for row in ledger_vs:
        pk = str(row["client__id"])
        name = row["client__name"]
        tmp_data[(pk, name)].append(row)

    for (pk, name), rows in tmp_data.items():
        data[pk] = {}
        data[pk]["id"] = pk
        data[pk]["name"] = name
        data[pk]["payment"] = 0
        data[pk]["billed_amount"] = 0
        data[pk]["current_balance"] = rows[0]["balance"]

        for i, row in enumerate(rows):
            data[pk]["payment"] += row["payment_amount"]
            data[pk]["billed_amount"] += row["bill_amount"]

        previous_balance = data[pk]["current_balance"]
        previous_balance += data[pk]["payment"]
        previous_balance -= data[pk]["billed_amount"]
        data[pk]["previous_balance"] = previous_balance

        total_payment += data[pk]["payment"]
        total_previous_balance += data[pk]["previous_balance"]
        total_current_balance += data[pk]["current_balance"]
        total_billed_amount += data[pk]["billed_amount"]

    columns = ["t.id", "t.client_id", "tt.name", "t.balance", "t.tx_time"]
    temp_table = "SELECT client_id, name, max(tx_time) AS tx_time, max(lc.id) AS id"
    temp_table += " FROM ledger_clientledger AS lc"
    temp_table += " JOIN clients_client AS cc ON(client_id=cc.id)"
    temp_table += " WHERE cc.shop_id=%d AND tx_date < '%s'" % (request.shop.id, str(selected_date))
    if len(data) != 0:
        temp_table += " AND client_id not in (%s)"
        temp_table = temp_table % ", ".join(data.keys())
    temp_table += " GROUP BY client_id, name"

    query = "SELECT %s FROM ledger_clientledger as t"
    query += " JOIN (%s) AS tt USING(id)"
    query = query % (", ".join(columns), temp_table)

    rows = ClientLedger.objects.raw(query)
    for row in rows:
        if row.balance == 0: continue
        pk = str(row.client_id)
        data[pk] = {}
        data[pk]["id"] = pk
        data[pk]["name"] = row.name
        data[pk]["current_balance"] = row.balance
        data[pk]["previous_balance"] = row.balance
        data[pk]["payment"] = 0
        data[pk]["billed_amount"] = 0

        print("row: ", row.id, row.name, row.balance, row.tx_time)
        total_previous_balance += row.balance
        total_current_balance += row.balance

    ledger_list = sorted(data.values(), key = lambda i: i['id'])
    context["ledger_list"] = ledger_list
    context["ledger_date"] = selected_date.strftime("%A, %d %B, %Y")
    context["total_payment"] = total_payment
    context["total_previous_balance"] = total_previous_balance
    context["total_current_balance"] = total_current_balance
    context["total_billed_amount"] = total_billed_amount
    return context

@login_required(login_url='/login/')
@require_http_methods(["GET"])
def clients_ledger_view(request):
    context = get_client_ledger_data(request)
    return render(request, 'ledger/clients_ledger_list.html', context)

@login_required(login_url='/login/')
@require_http_methods(["GET"])
def clients_ledger_print(request):
    context = get_client_ledger_data(request)
    data = []
    payment1 = 0
    payment2 = 0
    billed_amount1 = 0
    billed_amount2 = 0
    current_balance1 = 0
    current_balance2 = 0
    previous_balance1 = 0
    previous_balance2 = 0
    ledger_list1, ledger_list2 = [], []
    def append_page_total():
        nonlocal payment1, payment2
        nonlocal billed_amount1, billed_amount2
        nonlocal current_balance1, current_balance2
        nonlocal previous_balance1, previous_balance2
        ledger_list1.append({
            "id": "-",
            "name": "Total",
            "payment": payment1,
            "billed_amount": billed_amount1,
            "current_balance": current_balance1,
            "previous_balance": previous_balance1,
        })
        ledger_list2.append({
            "id": "-",
            "name": "Total",
            "payment": payment2,
            "billed_amount": billed_amount2,
            "current_balance": current_balance2,
            "previous_balance": previous_balance2,
        })
        payment1 = 0
        payment2 = 0
        billed_amount1 = 0
        billed_amount2 = 0
        current_balance1 = 0
        current_balance2 = 0
        previous_balance1 = 0
        previous_balance2 = 0

    for count, i in enumerate(context["ledger_list"]):
        if len(ledger_list1) == 36:
            append_page_total()
            data.append([ledger_list1, ledger_list2])
            ledger_list1, ledger_list2 = [], []
        elif count == 54:
            append_page_total()
            data.append([ledger_list1, ledger_list2])
            ledger_list1, ledger_list2 = [], []

        if count % 2 == 1:
            ledger_list1.append(i)
            payment1 += i["payment"] or 0
            billed_amount1 += i["billed_amount"] or 0
            current_balance1 += i["current_balance"] or 0
            previous_balance1 += i["previous_balance"] or 0
        else:
            ledger_list2.append(i)
            payment2 += i["payment"] or 0
            billed_amount2 += i["billed_amount"] or 0
            current_balance2 += i["current_balance"] or 0
            previous_balance2 += i["previous_balance"] or 0

    if len(ledger_list1) > 0 or len(ledger_list2) > 0:
        append_page_total()

    data.append([ledger_list1, ledger_list2])
    context["data"] = data
    return render(request, 'ledger/clients_ledger_print.html', context)
