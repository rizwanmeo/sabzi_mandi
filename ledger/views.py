import datetime

from django.db.models import Q
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django_filters.filterset import filterset_factory

from clients.models import Client
from suppliers.models import Supplier
from client_bills.models import ClientBill
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
    context = {}
    if request.method == "GET":
        data = {}
        qs = Client.objects.filter(shop=request.shop)
        qs = qs.filter(~Q(current_balance=0))
        vs = list(qs.values('name', 'id', 'current_balance'))

        for obj in vs:
            pk = obj["id"]
            name = obj["name"]
            balance = obj["current_balance"]
            data[pk] = {"id": pk, "name": name, "balance": balance}








        bill_date = request.GET.get("bill_date", "")
        if bill_date:
            qs = ClientBill.objects.filter(bill_date=bill_date)
        else:
            today = datetime.date.today()
            qs = ClientBill.objects.filter(bill_date=today)
        qs = qs.order_by("-id")
        vs = list(qs.values("client_id", "billed_amount", "balance", "payment__amount"))
        for obj in vs:
            pk = obj["client_id"]
            data[pk]["balance"] = obj["balance"]
            try:
                data[pk]["payment"] += obj["payment__amount"]
            except KeyError:
                data[pk]["payment"] = obj["payment__amount"]
            try:
                data[pk]["amount"] += obj["billed_amount"]
            except KeyError:
                data[pk]["amount"] = obj["billed_amount"]

        vs = list(data.values())
        context["ledger_list"] = vs
    return context

@login_required(login_url='/login/')
def clients_ledger_view(request):
    context = get_client_ledger_data(request)
    return render(request, 'ledger/clients_ledger_list.html', context)

@login_required(login_url='/login/')
def clients_ledger_print(request):
    context = get_client_ledger_data(request)
    vs = list(context["ledger_list"])
    ledger_list1, ledger_list2 = vs[:int(len(vs)/2)], vs[int(len(vs)/2):]
    context["ledger_list1"] = ledger_list1
    context["ledger_list2"] = ledger_list2[:-1]

    return render(request, 'ledger/clients_ledger_print.html', context)
