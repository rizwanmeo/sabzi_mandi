import datetime

from django import forms
from django.shortcuts import render
from django.contrib import messages
from django.db.models import Max, Sum
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, Http404, JsonResponse

from .forms import *
from .models import *
from sabzi_mandi.views import *
from ledger.models import ClientLedgerEditable
from ledger.utils import delete_ledger
from ledger.utils import create_payment_ledger, update_ledger_date


class ClientPaymentListView(CustomListView):
    model = ClientPayment
    template_name = "payments/client_payment_list.html"
    filterset_fields = ["client__name"]
    shop_lookup = "client__shop"

    def get_context_data(self, **kwargs):
        context = super(ClientPaymentListView, self).get_context_data(**kwargs)
        qs = context["object_list"]
        distinct_client_payments = list(qs.values('client').annotate(id=Max('id')))
        distinct_ids = [k['id'] for k in distinct_client_payments]
        qs = qs.filter(is_draft=False, id__in=distinct_ids)
        ## Getting list of client whose payment can be edit.
        object_list = []
        columns = ["id", "client__name", "client__id", "amount", "payment_date",
                   "payment_time", "description", "is_draft"]
        editable_payments = dict(ClientLedgerEditable.objects.values_list("client_id", "tx_id"))
        vs = list(qs.order_by("-id").values(*columns))
        for row in vs:
            row_data = {}
            row_data["id"] = row["id"]
            row_data["pk"] = row["id"]
            row_data["client"] = {"name": row["client__name"], "id": row["client__id"]}
            row_data["amount"] = row["amount"]
            row_data["payment_date"] = row["payment_date"]
            row_data["payment_time"] = row["payment_time"]
            row_data["description"] = row["description"]
            row_data["is_draft"] = row["is_draft"]

            # Checking client payment can be edit or not
            client_id = row["client__id"]
            payment_tx_id = "payment-"+str(row["id"])
            if payment_tx_id == editable_payments.get(client_id, ""):
                row_data["editable"] = True

            object_list.append(row_data)

        context["object_list"] = object_list
        return context

class ClientPaymentCreateView(CustomCreateView):
    model = ClientPayment
    success_url = "/payment/clients"
    template_name = "payments/client_payment_form.html"
    fields = ["client", "amount", "description", 'payment_date']

    def get_context_data(self, **kwargs):
        context = super(ClientPaymentCreateView, self).get_context_data(**kwargs)
        form = context["form"]
        choices = [("", "Select a Client")]
        form.fields["client"].widget.attrs["class"] = "fstdropdown-select"
        form.fields["client"].widget.attrs["required"] = False
        qs = form.fields["client"].queryset.filter(shop=self.request.shop)
        choices += list(qs.values_list("id", "name"))
        form.fields["client"].choices = choices
        form.fields["payment_date"].initial = datetime.date.today().strftime("%Y-%m-%d")
        return context

    def form_valid(self, form):
        super(ClientPaymentCreateView, self).form_valid(form)
        create_payment_ledger(form.instance, form.instance.client.current_balance)
        form.instance.client.current_balance -= form.instance.amount
        form.instance.client.save()
        msg = 'Client Payment: [%s] was creates succefully.' % form.instance.client.name
        messages.add_message(self.request, messages.INFO, msg)
        return HttpResponseRedirect(self.get_success_url())

class ClientPaymentUpdateView(CustomUpdateView):
    model = ClientPayment
    success_url = "/payment/clients"
    template_name = "payments/client_payment_form.html"
    fields = ["description", "payment_date"]

    def get_context_data(self, **kwargs):
        context = super(ClientPaymentUpdateView, self).get_context_data(**kwargs)
        try:
            payment_tx_id = "payment-"+str(self.object.pk)
            ClientLedgerEditable.objects.get(tx_id=payment_tx_id)
        except:
            raise Http404

        form = context["form"]
        form.initial["payment_date"] = form.initial["payment_date"].strftime("%Y-%m-%d")
        return context

    def form_valid(self, form):
        super(ClientPaymentUpdateView, self).form_valid(form)
        date = form.cleaned_data["payment_date"]
        description = form.cleaned_data["description"]
        update_ledger_date("payment-%d" % form.instance.pk, date, description)
        msg = 'Client Payment: [%s] was updated succefully.' % form.instance.client.name
        messages.add_message(self.request, messages.INFO, msg)
        return HttpResponseRedirect(self.get_success_url())

class ClientPaymentDeleteView(CustomDeleteView):
    model = ClientPayment
    success_url = "/payment/clients"

    def get_context_data(self, **kwargs):
        context = super(ClientPaymentDeleteView, self).get_context_data(**kwargs)
        try:
            payment_tx_id = "payment-"+str(self.object.pk)
            ClientLedgerEditable.objects.get(tx_id=payment_tx_id)
        except:
            raise Http404
        return context

    def delete(self, request, *args, **kwargs):
        super(ClientPaymentDeleteView, self).delete(request, *args, **kwargs)
        payment_tx_id = "payment-"+str(self.object.pk)
        delete_ledger(payment_tx_id)
        self.object.client.current_balance += self.object.amount
        self.object.client.save()
        msg = 'Client Payment: [%s] was deleted succfully.' % self.object.client.name
        messages.add_message(self.request, messages.INFO, msg)
        return HttpResponseRedirect(self.get_success_url())

class SupplierPaymentListView(CustomListView):
    model = SupplierPayment
    template_name = "payments/supplier_payment_list.html"
    filterset_fields = ["supplier__name"]
    shop_lookup = "supplier__shop"

class SupplierPaymentCreateView(CustomCreateView):
    model = SupplierPayment
    success_url = "/payment/suppliers"
    template_name = "payments/supplier_payment_form.html"
    fields = ['supplier', 'amount', 'payment_type', 'description', 'payment_date']

    def get_context_data(self, **kwargs):
        context = super(SupplierPaymentCreateView, self).get_context_data(**kwargs)
        form = context["form"]
        choices = [("", "Select a Supplier")]
        form.fields["supplier"].widget.attrs["class"] = "fstdropdown-select"
        qs = form.fields["supplier"].queryset.filter(shop=self.request.shop)
        choices += list(qs.values_list("id", "name"))
        form.fields["supplier"].choices = choices
        form.fields["payment_date"].initial = datetime.date.today().strftime("%Y-%m-%d")
        return context

    def form_valid(self, form):
        super(SupplierPaymentCreateView, self).form_valid(form)
        msg = 'Supplier Payment: [%s] was creates succefully.' % form.instance.supplier.name
        messages.add_message(self.request, messages.INFO, msg)
        return HttpResponseRedirect(self.get_success_url())

class SupplierPaymentDeleteView(CustomDeleteView):
    model = SupplierPayment
    success_url = "/payment/suppliers"

    def delete(self, request, *args, **kwargs):
        super(SupplierPaymentDeleteView, self).delete(request, *args, **kwargs)
        self.object.supplier.current_balance += self.object.amount
        self.object.supplier.save()
        msg = 'Supplier Payment: [%s] was deleted succfully.' % self.object.supplier.name
        messages.add_message(self.request, messages.INFO, msg)
        return HttpResponseRedirect(self.get_success_url())

def clients_payment_print(request):
    data = [[], []]
    context = {}
    if request.method == "GET":
        payment_date = request.GET.get("payment_date", "")
        if not payment_date:
            payment_date = datetime.datetime.today()

        qs = ClientPayment.objects.filter(client__shop=request.shop, payment_date=payment_date, is_draft=False)
        vs = list(qs.values('client__identifier', 'client__name').annotate(amount=Sum('amount')))

        for i, obj in enumerate(vs):
            row = {}
            row["client"] = {'id': obj["client__identifier"], 'name': obj["client__name"]}
            row["amount"] = obj["amount"]
            index = i % 2
            data[index].append(row)
        print('i', data)
        context["object_list"] = data
        return render(request, 'payments/clients_payment_print.html', context)

    return context

