import datetime
from collections import defaultdict

from django.db.models import Q
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django_filters.filterset import filterset_factory
from django.views.decorators.http import require_http_methods

from sabzi_mandi.views import *
from ledger.models import ClientLedger
from clients.models import Client
from suppliers.models import Supplier
from payments.models import SupplierPayment
from ledger.models import ClientLedger, SupplierLedgerEditable


class ClientLedgerListView(CustomListView):
    model = ClientLedger
    template_name = "client_bills/detail.html"

    def get_context_data(self, **kwargs):
        context = super(ClientLedgerListView, self).get_context_data(**kwargs)
        bill_date = self.request.GET.get("bill_date")

        data = []
        total_amount = 0
        vs = context["object_list"]
        #vs = vs.filter(tx_id__startswith="bill")
        vs = vs.filter(client__shop=self.request.shop, tx_id__startswith="bill", tx_date=bill_date).order_by("client__identifier")

        data = []
        object_list = []
        first_page_rows = 28
        rest_page_rows = 35
        for count, obj in enumerate(vs):
            row = {}
            row["tx_id"] = obj.tx_id
            row["description"] = obj.description

            if len(obj.description) > 80:
                if count < first_page_rows:
                    first_page_rows -= int(len(obj.description) / 80)
                else:
                    rest_page_rows -= int(len(obj.description) / 80)

            row["bill_amount"] = obj.bill_amount
            row["client"] = {"name": obj.client.name, "identifier": obj.client.identifier, "id": obj.client.id}
            total_amount += obj.bill_amount

            if count == first_page_rows:
                data.append(object_list)
                object_list = []
            elif count > first_page_rows and len(object_list) == rest_page_rows:
                data.append(object_list)
                object_list = []
                rest_page_rows = 35

            object_list.append(row)

        if len(object_list) > 0:
            data.append(object_list)

        context["logo_path"] = self.request.shop.logo.url
        context["data"] = data
        context["bill_date"] = bill_date
        context["total_amount"] = total_amount
        return context

def get_suppliers_ledger_data(request):
    data = []
    context = {}
    if request.method == "GET":
        total_received_amount = 0
        total_receivable_amount = 0
        supplier_id = request.GET.get("supplier", "")
        supplier_id=int(supplier_id) if supplier_id.isdigit() else 0
        qs = SupplierLedgerEditable.objects.filter(supplier__shop=request.shop)

        SupplierLedgerFilter = filterset_factory(model=SupplierLedgerEditable, fields=["supplier"])
        f = SupplierLedgerFilter(request.GET, queryset=qs)
        columns = ['supplier__name', 'supplier__id', 'supplier__identifier', 'balance', 'bill_amount', 'payment_amount', 'tx_date', 'tx_id']
        vs = list(f.qs.values(*columns).order_by('supplier__identifier'))
        for obj in vs:
            if obj["balance"] == 0:
                continue
            row = {}
            row["supplier"] = {"id": obj["supplier__identifier"], "pk": obj["supplier__id"], "name": obj["supplier__name"]}
            row["balance"] = obj["balance"]
            row["received_amount"] = round(obj["balance"], 2) if obj["balance"] > 0 else ""
            row["receivable_amount"] = round(-1*obj["balance"], 2) if obj["balance"] < 0 else ""
            row["bill_amount"] = round(obj["bill_amount"], 2)
            row["payment_amount"] = round(obj["payment_amount"], 2)
            row["tx_date"] = obj["tx_date"]
            row["tx_id"] = obj["tx_id"]
            data.append(row)
            total_received_amount += row["received_amount"] if row["received_amount"] else 0
            total_receivable_amount += row["receivable_amount"] if row["receivable_amount"] else 0

        context["ledger_list"] = data
        context["total_received_amount"] = round(total_received_amount, 2)
        context["total_receivable_amount"] = round(total_receivable_amount, 2)
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

    data = []
    received_amount = 0
    receiveable_amount = 0
    ledger_list1, ledger_list2 = [], []

    for count, i in enumerate(context["ledger_list"]):
        if len(ledger_list1) == 36:
            data.append([ledger_list1, ledger_list2])
            ledger_list1, ledger_list2 = [], []
        elif count == 54:
            data.append([ledger_list1, ledger_list2])
            ledger_list1, ledger_list2 = [], []

        if count % 2 == 1:
            ledger_list1.append(i)
        else:
            ledger_list2.append(i)

    data.append([ledger_list1, ledger_list2])
    context["data"] = data

    today = datetime.date.today()
    selected_date = request.GET.get("ledger_date", "")
    if selected_date == "":
        selected_date = today
    else:
        try:
            selected_date = datetime.datetime.strptime(selected_date, "%Y-%m-%d").date()
        except ValueError:
            selected_date = today

    context["logo_path"] = request.shop.logo.url
    context["ledger_date"] = selected_date.strftime("%A, %d %B, %Y")
    context["selected_date"] = selected_date.strftime("%Y-%m-%d")
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
    columns = ["client__id", "client__name", "client__identifier", "balance", "payment_amount", "bill_amount"]
    ledger_qs = ledger_qs.order_by("client", "-tx_time")
    ledger_vs = ledger_qs.values(*columns)

    tmp_data = defaultdict(list)
    for row in ledger_vs:
        pk = str(row["client__id"])
        name = row["client__name"]
        identifier = row["client__identifier"]
        tmp_data[(pk, identifier, name)].append(row)

    for (pk, identifier, name), rows in tmp_data.items():
        data[pk] = {}
        data[pk]["id"] = int(pk)
        data[pk]["name"] = name
        data[pk]["identifier"] = int(identifier)
        data[pk]["payment"] = 0
        data[pk]["billed_amount"] = 0
        data[pk]["current_balance"] = rows[0]["balance"]

        for i, row in enumerate(rows):
            data[pk]["payment"] += row["payment_amount"]
            data[pk]["billed_amount"] += row["bill_amount"]

        previous_balance = data[pk]["current_balance"]
        previous_balance += data[pk]["payment"]
        previous_balance -= data[pk]["billed_amount"]
        data[pk]["previous_balance"] = round(previous_balance, 2)

        total_payment += data[pk]["payment"]
        total_previous_balance += data[pk]["previous_balance"]
        total_current_balance += data[pk]["current_balance"]
        total_billed_amount += data[pk]["billed_amount"]

    # request.shop can be None do need to check first if shop exists
    shop_id = request.shop.id if request.shop else 0

    columns = ["t.id", "t.client_id", "tt.identifier", "tt.name", "t.balance", "t.tx_time"]
    temp_table = "SELECT client_id, name, identifier, max(tx_time) AS tx_time, max(lc.id) AS id"
    temp_table += " FROM ledger_clientledger AS lc"
    temp_table += " JOIN clients_client AS cc ON(client_id=cc.id)"
    temp_table += " WHERE cc.shop_id=%d AND tx_date < '%s'" % (shop_id, str(selected_date))
    if len(data) != 0:
        temp_table += " AND client_id not in (%s)"
        temp_table = temp_table % ", ".join(data.keys())
    temp_table += " GROUP BY client_id, identifier, name"

    query = "SELECT %s FROM ledger_clientledger as t"
    query += " JOIN (%s) AS tt USING(id)"
    query = query % (", ".join(columns), temp_table)

    rows = ClientLedger.objects.raw(query)
    for row in rows:
        if row.balance == 0: continue
        pk = str(row.client_id)
        data[pk] = {}
        data[pk]["id"] = int(pk)
        data[pk]["name"] = row.name
        data[pk]["identifier"] = int(row.identifier)
        data[pk]["current_balance"] = round(row.balance, 2)
        data[pk]["previous_balance"] = round(row.balance, 2)
        data[pk]["payment"] = 0
        data[pk]["billed_amount"] = 0

        total_previous_balance += row.balance
        total_current_balance += row.balance

    ledger_list = sorted(data.values(), key = lambda i: i['identifier'])
    context["logo_path"] = request.shop.logo.url
    context["ledger_list"] = ledger_list
    context["ledger_date"] = selected_date.strftime("%A, %d %B, %Y")
    context["selected_date"] = selected_date.strftime("%Y-%m-%d")
    context["total_payment"] = round(total_payment, 2)
    context["total_previous_balance"] = round(total_previous_balance, 2)
    context["total_current_balance"] = round(total_current_balance, 2)
    context["total_billed_amount"] = round(total_billed_amount, 2)
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
            "payment": round(payment1, 2),
            "billed_amount": round(billed_amount1, 2),
            "current_balance": round(current_balance1, 2),
            "previous_balance": round(previous_balance1, 2),
        })
        ledger_list2.append({
            "id": "-",
            "name": "Total",
            "payment": round(payment2, 2),
            "billed_amount": round(billed_amount2, 2),
            "current_balance": round(current_balance2, 2),
            "previous_balance": round(previous_balance2, 2),
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
