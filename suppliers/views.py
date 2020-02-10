from django.db.models import Sum, Count
from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, Http404, JsonResponse
from django.views.generic import CreateView, UpdateView, DeleteView

from .models import *
from django_filters.views import FilterView
from sabzi_mandi.views import CustomLoginRequiredMixin

class SupplierListView(FilterView, CustomLoginRequiredMixin):
    model = Supplier
    template_name = "suppliers/list.html"
    filterset_fields = ["name"]

    def get_context_data(self, **kwargs):
        context = super(SupplierListView, self).get_context_data(**kwargs)
        object_list = context["object_list"]
        object_list = object_list.filter(shop=self.request.shop)
        context["object_list"] = object_list
        return context

class SupplierCreateView(CustomLoginRequiredMixin, CreateView):
    model = Supplier
    success_url = "/suppliers"
    template_name = "suppliers/form.html"
    fields = ["name", "address", "cnic", "phone", "opening_balance"]

    def form_valid(self, form):
        form.instance.shop_id = 1
        super(SupplierCreateView, self).form_valid(form)
        msg = 'Supplier: [%s] was created succfully.' % form.instance.name
        messages.add_message(self.request, messages.INFO, msg)
        return HttpResponseRedirect(self.get_success_url())

class SupplierUpdateView(CustomLoginRequiredMixin, UpdateView):
    model = Supplier
    success_url = "/suppliers"
    template_name = "suppliers/form.html"
    fields = ["name", "address", "cnic", "phone", "opening_balance"]

    def form_valid(self, form):
        form.instance.last_modified = datetime.datetime.now()
        super(ClientUpdateView, self).form_valid(form)
        msg = 'Supplier: [%s] was updated succfully.' % form.instance.name
        messages.add_message(self.request, messages.INFO, msg)
        return HttpResponseRedirect(self.get_success_url())
