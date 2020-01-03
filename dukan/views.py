from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import JsonResponse
from django.http import HttpResponseRedirect
from django.views.generic import ListView, CreateView, UpdateView

from dukan.models import *

@login_required(login_url='/login/')
def index(request):
    context = {
        'name': 'Muhammad Rizwan',
        'daily_earn': '4,000',
        'monthly_earn': '74,000',
        'daily_purchase': '3,000',
        'monthly_purchase': '50,000',
    }

    shops = list(request.user.shop_set.values("id", "name"))
    context["shops_list"] = shops
    return render(request, 'index.html', context)

@login_required(login_url='/login/')
def make_default_shop(request):
    shop_id = request.POST.get("shop_id", 0)
    shop = Shop.objects.get(id=shop_id)
    if request.method == "POST":
        Shop.objects.filter(is_default=True).update(is_default=False)
        shop.is_default = True
        shop.save()
        msg = 'Shop: [%s] was set to default.' % shop.name
        messages.add_message(request, messages.INFO, msg)
    else:
        msg = 'Error: Request was invalid for shop [%s].' % shop.name
        messages.add_message(request, messages.ERROR, msg)
    return HttpResponseRedirect("/shops")


@login_required(login_url='/login/')
def get_earn_data(request):
    data = [1000, 2000, 3000,4000, 5000, 6000, 7000, 8000, 9000, 9000, 9000, 9000]
    labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    max_value = 9000
    return JsonResponse({"status": True, "data": data, "labels": labels, "max_value": max_value})

@login_required(login_url='/login/')
def get_top_client(request):
    data = [1000, 2000, 3000,4000, 5000, 6000, 7000, 8000, 9000, 9000, 9000, 9000]
    labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    max_value = 9000
    return JsonResponse({"status": True, "data": data, "labels": labels, "max_value": max_value})

class CustomLoginRequiredMixin(LoginRequiredMixin):
    login_url = "/login"

class ShopListView(CustomLoginRequiredMixin, ListView):
    model = Shop
    template_name = "shops/list.html"

class ShopCreateView(CustomLoginRequiredMixin, CreateView):
    model = Shop
    success_url = "/shops"
    template_name = "shops/form.html"
    fields = ["name", "address", "logo"]

    def form_valid(self, form):
        form.instance.owner = self.request.user
        if form.instance.logo:
            form.instance.make_thumbnail()
        super(ShopCreateView, self).form_valid(form)
        msg = 'Shop: [%s] was creates succfully.' % form.instance.name
        messages.add_message(self.request, messages.INFO, msg)
        return HttpResponseRedirect(self.get_success_url())

class ShopUpdateView(CustomLoginRequiredMixin, UpdateView):
    model = Shop
    success_url = "/shops"
    template_name = "shops/form.html"
    fields = ["name", "address", "logo"]

    def form_valid(self, form):
        form.instance.make_thumbnail()
        form.instance.last_modified = datetime.datetime.now()
        super(ClientUpdateView, self).form_valid(form)
        msg = 'Shop: [%s] was updated succfully.' % form.instance.name
        messages.add_message(self.request, messages.INFO, msg)
        return HttpResponseRedirect(self.get_success_url())

class SupplierListView(CustomLoginRequiredMixin, ListView):
    model = Supplier
    template_name = "suppliers/list.html"

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

class ClientListView(CustomLoginRequiredMixin, ListView):
    model = Client
    template_name = "clients/list.html"

class ClientCreateView(CustomLoginRequiredMixin, CreateView):
    model = Client
    success_url = "/clients"
    template_name = "clients/form.html"
    fields = ["name", "address", "cnic", "phone", "opening_balance"]

    def form_valid(self, form):
        form.instance.shop_id = 1
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
