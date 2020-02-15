from django.db.models import Sum, Count
from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, Http404, JsonResponse
from django.views.generic import CreateView, UpdateView, DeleteView

from .models import *
from .forms import *
from django_filters.views import FilterView
from sabzi_mandi.views import CustomLoginRequiredMixin


class ClientPaymentListView(CustomLoginRequiredMixin, FilterView):
    model = ClientPayment
    template_name = "payments/client_payment_list.html"
    filterset_fields = ["client__name"]


class ClientPaymentCreateView(CustomLoginRequiredMixin, CreateView):
    model = ClientPayment
    success_url = "/payments/clients"
    template_name = "payments/client_payment_form.html"
    fields = ["client", "amount", "description"]

    def get_context_data(self, **kwargs):
        context = super(ClientPaymentCreateView, self).get_context_data(**kwargs)
        form = context["form"]
        choices = [("", "Select a Client")]
        form.fields["client"].widget.attrs["class"] = "fstdropdown-select"
        qs = form.fields["client"].queryset.filter(shop=self.request.shop)
        choices += list(qs.values_list("id", "name"))
        form.fields["client"].choices = choices
        return context

    def form_valid(self, form):
        msg = 'Payment: [%s] was creates succefully.' % form.instance.name
        messages.add_message(self.request, messages.INFO, msg)
        return HttpResponseRedirect(self.get_success_url())


class SupplierPaymentListView(CustomLoginRequiredMixin, FilterView):
    model = SupplierPayment
    template_name = "payments/supplier_payment_list.html"
    filterset_fields = ["supplier__name"]

class SupplierPaymentCreateView(CustomLoginRequiredMixin, CreateView):
    model = SupplierPayment
    success_url = "/payments/suppliers"
    template_name = "payments/supplier_payment_form.html"
    fields = ['supplier', 'amount', 'payment_type', 'description']

    def get_context_data(self, **kwargs):
        context = super(SupplierPaymentCreateView, self).get_context_data(**kwargs)
        form = context["form"]
        choices = [("", "Select a Supplier")]
        form.fields["supplier"].widget.attrs["class"] = "fstdropdown-select"
        qs = form.fields["supplier"].queryset.filter(shop=self.request.shop)
        choices += list(qs.values_list("id", "name"))
        form.fields["supplier"].choices = choices
        return context

    def form_valid(self, form):
        msg = 'Payment: [%s] was creates succefully.' % form.instance.name
        messages.add_message(self.request, messages.INFO, msg)
        return HttpResponseRedirect(self.get_success_url())
