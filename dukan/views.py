from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.generic import ListView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin

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
    return render(request, 'index.html', context)


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

@login_required(login_url='/login/')
def get_suppliers(request):
    context = {}
    return render(request, 'supplier.html', context)

@login_required(login_url='/login/')
def get_clients(request):
    context = {}
    return render(request, 'client.html', context)


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
        super(ShopCreateView, self).form_valid(form)
        return HttpResponseRedirect(self.get_success_url())

class ShopUpdateView(CustomLoginRequiredMixin, UpdateView):
    model = Shop
    success_url = "/shops"
    template_name = "shops/form.html"
    fields = ["name", "address", "logo"]
