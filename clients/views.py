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

class ClientListView(CustomLoginRequiredMixin, FilterView):
    model = Client
    template_name = "clients/list.html"
    filterset_fields = ["name"]

    def get_context_data(self, **kwargs):
        context = super(ClientListView, self).get_context_data(**kwargs)
        object_list = context["object_list"]
        object_list = object_list.filter(shop=self.request.shop)
        context["object_list"] = object_list
        return context

class ClientCreateView(CustomLoginRequiredMixin, CreateView):
    model = Client
    success_url = "/clients"
    template_name = "clients/form.html"
    fields = ["name", "address", "cnic", "phone", "opening_balance"]

    def form_valid(self, form):
        form.instance.shop_id = 1
        form.instance.current_balance = form.instance.opening_balance
        super(ClientCreateView, self).form_valid(form)
        msg = 'Client: [%s] was created succfully.' % form.instance.name
        messages.add_message(self.request, messages.INFO, msg)
        return HttpResponseRedirect(self.get_success_url())

class ClientUpdateView(CustomLoginRequiredMixin, UpdateView):
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
