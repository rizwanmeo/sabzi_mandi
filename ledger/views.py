import datetime
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from client_bills.models import ClientBill

@login_required(login_url='/login/')
def ledger_print(request):
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

    return render(request, 'ledger/print.html', context)

@login_required(login_url='/login/')
def ledger_view(request):
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

    return render(request, 'ledger/list.html', context)
