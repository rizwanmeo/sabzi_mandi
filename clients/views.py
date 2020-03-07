from django.db.models import Sum, Count
from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, Http404, JsonResponse

from .models import *
from sabzi_mandi.views import *

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
