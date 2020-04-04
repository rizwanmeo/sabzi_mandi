import datetime

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
    kwargs = {"client__shop": request.shop, "tx_date": today}
    ledger_qs = ClientLedger.objects.filter(**kwargs)
    columns = ["client__id", "client__name", "balance", "payment_amount", "bill_amount"]
    ledger_vs = ledger_qs.order_by("client", "-tx_date").values(*columns)

    for row in ledger_vs:
        pk = str(row["client__id"])
        if pk not in data:
            data[pk] = {}
            data[pk]["id"] = pk
            data[pk]["name"] = row["client__name"]
            data[pk]["current_balance"] = row["balance"]
            data[pk]["payment"] = 0
            data[pk]["billed_amount"] = 0
            data[pk]["previous_balance"] = 0
        else:
            current_balance = row[pk]["balance"]
            payment = data[pk]["payment_amount"]
            billed_amount = row[pk]["bill_amount"]
            previous_balance = current_balance + payment - billed_amount
            data[pk]["payment"] += payment
            data[pk]["billed_amount"] += billed_amount
            data[pk]["previous_balance"] = previous_balance

            total_payment += payment
            total_previous_balance += previous_balance
            total_current_balance += current_balance
            total_billed_amount += billed_amount

    from django.db import connection

    columns = ["t.client_id", "tt.name", "t.balance"]
    temp_table = "SELECT client_id, name, max(tx_time) AS tx_time FROM ledger_clientledger"
    temp_table += " JOIN clients_client AS c ON(client_id=c.id)"
    temp_table += " WHERE c.shop_id=%d" % request.shop.id
    if len(data) != 0:
        temp_table += " AND client_id in (%s) AND tx_date < '%s'"
        temp_table = temp_table % (", ".join(data.keys()), str(today))
    temp_table += " GROUP BY client_id, name"

    query = "SELECT %s FROM ledger_clientledger as t"
    query += " JOIN (%s) AS tt USING(client_id, tx_time)"
    query = query % (", ".join(columns), temp_table)

    cursor = connection.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()

    for row in rows:
        pk = str(row[0])
        data[pk] = {}
        data[pk]["id"] = pk
        data[pk]["name"] = row[1]
        data[pk]["current_balance"] = row[2]
        data[pk]["previous_balance"] = row[2]
        data[pk]["payment"] = 0
        data[pk]["billed_amount"] = 0

        total_previous_balance += row[2]
        total_current_balance += row[2]

    ledger_list = sorted(data.values(), key = lambda i: i['id'])
    context["ledger_list"] = ledger_list
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
    ledger_list1, ledger_list2 = [], []
    for count, i in enumerate(context["ledger_list"]):
        if len(ledger_list1) == 38:
            data.append([ledger_list1, ledger_list2])
            ledger_list1, ledger_list2 = [], []
        elif count == 56:
            data.append([ledger_list1, ledger_list2])
            ledger_list1, ledger_list2 = [], []

        if count % 2 == 1:
            ledger_list1.append(i)
        else:
            ledger_list2.append(i)

    today = datetime.date.today()
    data.append([ledger_list1, ledger_list2])
    context["data"] = data
    context["ledger_date"] = today.strftime("%A, %d %B, %Y")
    return render(request, 'ledger/clients_ledger_print.html', context)
