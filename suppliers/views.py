import datetime

from django.db.models import Sum, Count
from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import HttpResponseRedirect, Http404, JsonResponse

from .models import *
from sabzi_mandi.views import *
from bills import supplier_utils
from ledger.utils import create_supplier_opening_ledger

class SupplierListView(CustomListView):
    model = Supplier
    template_name = "suppliers/list.html"
    filterset_fields = ["name"]
    shop_lookup = "shop"

    def get_context_data(self, **kwargs):
        context = super(SupplierListView, self).get_context_data(**kwargs)
        return context


class SupplierCreateView(CustomCreateView):
    model = Supplier
    success_url = "/suppliers"
    template_name = "suppliers/form.html"
    fields = ["name", "address", "cnic", "phone", "opening_balance", "created_time"]

    def form_valid(self, form):
        form.instance.shop = self.request.shop
        form.instance.current_balance = form.instance.opening_balance
        last_supplier = Supplier.objects.filter(shop=self.request.shop).order_by("-identifier").first()
        if last_supplier:
            form.instance.identifier = last_supplier.identifier + 1
        else:
            form.instance.identifier = 1
        super(SupplierCreateView, self).form_valid(form)
        create_supplier_opening_ledger(form.instance)
        msg = 'Supplier: [%s] was created succfully.' % form.instance.name
        messages.add_message(self.request, messages.INFO, msg)
        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super(SupplierCreateView, self).get_context_data(**kwargs)
        form = context["form"]
        created_time = datetime.date.today().strftime("%Y-%m-%d")
        form.fields["created_time"].initial = created_time
        return context


class SupplierUpdateView(CustomUpdateView):
    model = Supplier
    success_url = "/suppliers"
    template_name = "suppliers/form.html"
    fields = ["name", "address", "cnic", "phone", "opening_balance", "created_time"]

    def form_valid(self, form):
        form.instance.last_modified = datetime.datetime.now()
        super(SupplierUpdateView, self).form_valid(form)
        msg = 'Supplier: [%s] was updated succfully.' % form.instance.name
        messages.add_message(self.request, messages.INFO, msg)
        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super(SupplierUpdateView, self).get_context_data(**kwargs)
        form = context["form"]
        created_time = form.initial["created_time"].date().strftime("%Y-%m-%d")
        form.initial["created_time"] = created_time
        return context

class SupplierDeleteView(CustomDeleteView):
    model = Supplier
    success_url = "/suppliers"

    def delete(self, request, *args, **kwargs):
        super(SupplierDeleteView, self).delete(request, *args, **kwargs)
        msg = 'Supplier: [%s] was delete succfully.' % self.object.name
        messages.add_message(self.request, messages.INFO, msg)
        return HttpResponseRedirect(self.get_success_url())


class SupplierDetailView(CustomDetailView):
    model = Supplier
    template_name = "suppliers/detail.html"

    def get_context_data(self, **kwargs):
        context = super(SupplierDetailView, self).get_context_data(**kwargs)
        return supplier_utils.get_supplier_detail(self.request, context, True)

class SupplierDetailPrintView(CustomDetailView):
    model = Supplier
    template_name = "suppliers/detail-print.html"

    def get_context_data(self, **kwargs):
        context = super(SupplierDetailPrintView, self).get_context_data(**kwargs)
        context["logo_path"] = self.request.shop.logo.url
        return supplier_utils.get_supplier_detail(self.request, context)
