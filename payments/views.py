import datetime

from django import forms
from django.db.models import Sum, Count
from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, Http404, JsonResponse

from .forms import *
from .models import *
from sabzi_mandi.views import *


class ClientPaymentListView(CustomListView):
    model = ClientPayment
    template_name = "payments/client_payment_list.html"
    filterset_fields = ["client__name"]


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
        form.instance.client.current_balance -= form.instance.amount
        form.instance.client.save()
        msg = 'Client Payment: [%s] was creates succefully.' % form.instance.client.name
        messages.add_message(self.request, messages.INFO, msg)
        return HttpResponseRedirect(self.get_success_url())


class SupplierPaymentListView(CustomListView):
    model = SupplierPayment
    template_name = "payments/supplier_payment_list.html"
    filterset_fields = ["supplier__name"]

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
