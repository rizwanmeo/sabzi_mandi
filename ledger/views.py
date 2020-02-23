import datetime

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django_filters.filterset import filterset_factory

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

@login_required(login_url='/login/')
def clients_ledger_view(request):
    context = {}
    if request.method == "GET":
        today = datetime.date.today()
        filter_kwargs = {
            "client__shop": request.shop,
            "is_draft": False,
            #"bill_time__gt": today,
        }

        data = {}
        client_bill_qs = ClientBill.objects.filter(**filter_kwargs)
        columns = ['client__name', 'client__id', 'client__current_balance', 'billed_amount']
        client_bill_vs = client_bill_qs.values(*columns)
        for obj in client_bill_vs:
            pk = obj["client__id"]
            name = obj["client__name"]
            amount = obj["billed_amount"]
            balance = obj["client__current_balance"]
            try:
                data[pk]["amount"] += amount
                data[pk]["balance"] = data[pk]["balance"]+amount
            except:
                data[pk] = {"id": pk, 
                            "name": name, 
                            "amount": amount, 
                            "balance": balance+amount,
                            "total": balance}
        vs = list(data.values())
        context["ledger_list"] = vs

    return render(request, 'ledger/clients_ledger_list.html', context)

@login_required(login_url='/login/')
def clients_ledger_print(request):
    context = {}
    if request.method == "GET":
        today = datetime.date.today()
        filter_kwargs = {
            "client__shop": request.shop,
            "is_draft": False,
            #"bill_time__gt": today,
        }

        data = {}
        client_bill_qs = ClientBill.objects.filter(**filter_kwargs)
        columns = ['client__name', 'client__id', 'client__current_balance', 'billed_amount']
        client_bill_vs = client_bill_qs.values(*columns)
        for obj in client_bill_vs:
            pk = obj["client__id"]
            name = obj["client__name"]
            amount = obj["billed_amount"]
            balance = obj["client__current_balance"]
            try:
                data[pk]["amount"] += amount
                data[pk]["balance"] = data[pk]["balance"]+amount
            except:
                data[pk] = {"id": pk, 
                            "name": name, 
                            "amount": amount, 
                            "balance": balance+amount,
                            "total": balance}
        vs = list(data.values())
        ledger_list1, ledger_list2 = vs[:int(len(vs)/2)], vs[int(len(vs)/2):]
        context["ledger_list1"] = ledger_list1
        context["ledger_list2"] = ledger_list2[:-1]

    return render(request, 'ledger/clients_ledger_print.html', context)
