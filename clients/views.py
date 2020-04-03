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
    fields = ["name", "address", "cnic", "phone", "opening_balance"]

    def form_valid(self, form):
        form.instance.shop = self.request.shop
        form.instance.current_balance = form.instance.opening_balance
        super(ClientCreateView, self).form_valid(form)
        create_opening_ledger(form.instance)
        msg = 'Client: [%s] was created succfully.' % form.instance.name
        messages.add_message(self.request, messages.INFO, msg)
        return HttpResponseRedirect(self.get_success_url())

class ClientUpdateView(CustomUpdateView):
    model = Client
    success_url = "/clients"
    template_name = "clients/form.html"
    fields = ["name", "address", "cnic", "phone", "opening_balance"]

    def form_valid(self, form):
        form.instance.last_modified = datetime.datetime.now()
        super(ClientUpdateView, self).form_valid(form)
        msg = 'Client: [%s] was updated succfully.' % form.instance.name
        messages.add_message(self.request, messages.INFO, msg)
        return HttpResponseRedirect(self.get_success_url())

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


class ClientDetailView(CustomDetailView):
    model = Client
    template_name = "clients/detail.html"

    def get_context_data(self, **kwargs):
        context = super(ClientDetailView, self).get_context_data(**kwargs)
        obj = context["object"]
        qs = obj.clientledger_set.all()
        qs = qs.order_by("id")
        context["data"] = qs
        return context

class ClientDetailPrintView(CustomDetailView):
    model = Client
    template_name = "clients/detail-print.html"

    def get_context_data(self, **kwargs):
        context = super(ClientDetailPrintView, self).get_context_data(**kwargs)
        obj = context["object"]
        columns = ["client__id", "client__name", "tx_id", "tx_time", "tx_date",
                   "balance", "bill_amount", "payment_amount", "description"]

        qs = obj.clientledger_set.all()
        qs = qs.order_by("id")
        vs = list(qs.values(*columns))

        data = []
        object_list = []
        total_payment = 0
        total_billed_amount = 0
        for count, row in enumerate(vs):
            if count == 28:
                data.append(object_list)
                object_list = []
            elif count > 28 and len(object_list) == 38:
                data.append(object_list)
                object_list = []
            row["client"] = {"id": row.pop("client__id"), "name": row.pop("client__name")}
            object_list.append(row)

            total_payment += row["payment_amount"]
            total_billed_amount += row["bill_amount"]

        if len(object_list) > 0:
            data.append(object_list)

        context["data"] = data
        context["total_payment"] = total_payment
        context["total_billed_amount"] = total_billed_amount

        return context
