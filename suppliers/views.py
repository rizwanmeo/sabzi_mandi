import datetime

from django.db.models import Sum, Count
from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, Http404, JsonResponse

from .models import *
from sabzi_mandi.views import *

class SupplierListView(CustomListView):
    model = Supplier
    template_name = "suppliers/list.html"
    filterset_fields = ["name"]
    shop_lookup = "shop"

class SupplierCreateView(CustomCreateView):
    model = Supplier
    success_url = "/suppliers"
    template_name = "suppliers/form.html"
    fields = ["name", "address", "cnic", "phone", "opening_balance"]

    def form_valid(self, form):
        form.instance.shop = self.request.shop
        form.instance.current_balance = form.instance.opening_balance
        last_supplier = Supplier.objects.filter(shop=self.request.shop).order_by("-identifier").first() 
        form.instance.identifier = last_supplier.identifier + 1
        super(SupplierCreateView, self).form_valid(form)
        msg = 'Supplier: [%s] was created succfully.' % form.instance.name
        messages.add_message(self.request, messages.INFO, msg)
        return HttpResponseRedirect(self.get_success_url())

class SupplierUpdateView(CustomUpdateView):
    model = Supplier
    success_url = "/suppliers"
    template_name = "suppliers/form.html"
    fields = ["name", "address", "cnic", "phone", "opening_balance"]

    def form_valid(self, form):
        form.instance.last_modified = datetime.datetime.now()
        super(SupplierUpdateView, self).form_valid(form)
        msg = 'Supplier: [%s] was updated succfully.' % form.instance.name
        messages.add_message(self.request, messages.INFO, msg)
        return HttpResponseRedirect(self.get_success_url())

class SupplierDeleteView(CustomDeleteView):
    model = Supplier
    success_url = "/suppliers"

    def delete(self, request, *args, **kwargs):
        super(SupplierDeleteView, self).delete(request, *args, **kwargs)
        msg = 'Supplier: [%s] was delete succfully.' % self.object.name
        messages.add_message(self.request, messages.INFO, msg)
        return HttpResponseRedirect(self.get_success_url())
