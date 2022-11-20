import datetime

from django.db.models import Sum, Count
from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, Http404, JsonResponse

from .models import *
from sabzi_mandi.views import *
from client_bills.models import ClientBill
from ledger.utils import create_opening_ledger

class ClientListView(CustomListView):
    model = Client
    template_name = "clients/list.html"
    filterset_fields = ["name"]
    shop_lookup = "shop"

class ClientCreateView(CustomCreateView):
    model = Client
    success_url = "/clients"
    template_name = "clients/form.html"
    fields = ["name", "address", "cnic", "phone", "opening_balance", "created_time"]

    def form_valid(self, form):
        form.instance.shop = self.request.shop
        form.instance.current_balance = form.instance.opening_balance
        last_client = Client.objects.filter(shop=self.request.shop).order_by("-identifier").first() 
        form.instance.identifier = last_client.identifier + 1

        super(ClientCreateView, self).form_valid(form)
        create_opening_ledger(form.instance)
        msg = 'Client: [%s] was created succfully.' % form.instance.name
        messages.add_message(self.request, messages.INFO, msg)
        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super(ClientCreateView, self).get_context_data(**kwargs)
        form = context["form"]
        created_time = datetime.date.today().strftime("%Y-%m-%d")
        form.fields["created_time"].initial = created_time
        return context

class ClientUpdateView(CustomUpdateView):
    model = Client
    success_url = "/clients"
    template_name = "clients/form.html"
    fields = ["name", "address", "cnic", "phone", "opening_balance", "created_time"]

    def form_valid(self, form):
        super(ClientUpdateView, self).form_valid(form)
        msg = 'Client: [%s] was updated succfully.' % form.instance.name
        messages.add_message(self.request, messages.INFO, msg)
        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super(ClientUpdateView, self).get_context_data(**kwargs)
        form = context["form"]
        created_time = form.initial["created_time"].date().strftime("%Y-%m-%d")
        form.initial["created_time"] = created_time
        return context

class ClientDeleteView(CustomDeleteView):
    model = Client
    success_url = "/clients"

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        super(ClientDeleteView, self).delete(request, *args, **kwargs)
        msg = 'Client: [%s] was delete succfully.' % self.object.name
        messages.add_message(self.request, messages.INFO, msg)
        return HttpResponseRedirect(self.get_success_url())


def get_client_detail(request, context, is_reverse=True):
    obj = context["object"]

    columns = ["id", "client__id", "client__name", "tx_id", "tx_time", "tx_date",
               "balance", "bill_amount", "payment_amount", "description"]

    qs = obj.clientledger_set.all()
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

    qs = qs.order_by("-id" if is_reverse else "id")
    vs = list(qs.values(*columns))

    data = []
    total_payment = 0
    opening_balance = 0
    current_balance = 0
    total_billed_amount = 0

    for row in vs:
        row["client"] = {"id": row.pop("client__id"), "name": row.pop("client__name")}
        data.append(row)
        total_payment += row["payment_amount"]
        total_billed_amount += row["bill_amount"]

    if len(data) > 0:
        if is_reverse:
            opening_balance = data[-1]["balance"] + data[-1]["payment_amount"] - data[-1]["bill_amount"]
            current_balance = data[0]["balance"]
        else:
            opening_balance = data[0]["balance"] + data[0]["payment_amount"] - data[0]["bill_amount"]
            current_balance = data[-1]["balance"]

    context["data"] = data
    context["start_date"] = start_date
    context["end_date"] = end_date
    context["total_payment"] = total_payment
    context["total_billed_amount"] = total_billed_amount
    context["opening_balance"] = opening_balance
    context["current_balance"] = current_balance
    context["detail_duration"] = detail_duration

    return context

class ClientDetailView(CustomDetailView):
    model = Client
    template_name = "clients/detail.html"

    def get_context_data(self, **kwargs):
        context = super(ClientDetailView, self).get_context_data(**kwargs)
        return get_client_detail(self.request, context)

class ClientDetailPrintView(CustomDetailView):
    model = Client
    template_name = "clients/detail-print.html"

    def get_context_data(self, **kwargs):
        context = super(ClientDetailPrintView, self).get_context_data(**kwargs)
        obj = context["object"]
        context = get_client_detail(self.request, context, False)
        vs = context["data"]

        data = []
        object_list = []
        for count, row in enumerate(vs):
            if count == 28:
                data.append(object_list)
                object_list = []
            elif count > 28 and len(object_list) == 38:
                data.append(object_list)
                object_list = []
            object_list.append(row)

        if len(object_list) > 0:
            data.append(object_list)

        context["data"] = data
        return context
