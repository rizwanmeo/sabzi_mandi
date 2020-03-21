import datetime

from django.db.models import Q
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django_filters.filterset import filterset_factory

from clients.models import Client
from suppliers.models import Supplier
from client_bills.models import ClientBill
from payments.models import ClientPayment, SupplierPayment


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
    context = {}
    if request.method == "GET":
        data = {}
        qs = Client.objects.filter(shop=request.shop)
        qs = qs.filter(~Q(current_balance=0))
        client_vs = list(qs.values('id', 'name', 'current_balance'))
        for obj in client_vs:
            pk = obj["id"]
            data[pk] = {}
            data[pk]["id"] = obj["id"]
            data[pk]["name"] = obj["name"]
            data[pk]["previous_balance"] = 0
            data[pk]["current_balance"] = obj["current_balance"]
            data[pk]["payment"] = 0
            data[pk]["billed_amount"] = 0

        today = datetime.date.today()
        bill_kwargs = {"client__shop": request.shop, "created_time__gte": today}
        bill_qs = ClientBill.objects.filter(**bill_kwargs)
        bill_vs = list(bill_qs.values("client_id", "billed_amount"))
        for obj in bill_vs:
            client_id = obj["client_id"]
            data[client_id]["billed_amount"] += obj["billed_amount"]

        payment_kwargs = {"client__shop": request.shop, "payment_time__gte": today}
        payment_qs = ClientPayment.objects.filter(**payment_kwargs)
        payment_qs = list(payment_qs.values("client_id", "amount"))
        for obj in payment_qs:
            client_id = obj["client_id"]
            data[client_id]["payment"] += obj["amount"]

        ledger_list = []
        for pk in data:
            billed_amount = data[pk]["billed_amount"]
            current_balance = data[pk]["current_balance"]
            payment = data[pk]["payment"]
            data[pk]["previous_balance"] = current_balance + payment - billed_amount
            ledger_list.append(data[pk])

        ledger_list = sorted(ledger_list, key = lambda i: i['id']) 
        context["ledger_list"] = ledger_list
    return context

@login_required(login_url='/login/')
def clients_ledger_view(request):
    context = get_client_ledger_data(request)
    return render(request, 'ledger/clients_ledger_list.html', context)

@login_required(login_url='/login/')
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
