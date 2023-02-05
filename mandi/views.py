import datetime

from django.db.models import Sum, Count
from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, Http404, JsonResponse
from django.views.generic import CreateView, UpdateView, DeleteView
from django_filters.views import FilterView

from .models import *
from bills.models import ClientBill

@login_required(login_url='/login/')
def index(request):
    today = datetime.date.today()
    month = today.replace(day=1)

    client_bill_qs = ClientBill.objects.filter(is_draft=False, bill_date__gt=today)
    today_billed_amount = client_bill_qs.aggregate(amount=Sum('billed_amount'))

    client_bill_qs = ClientBill.objects.filter(is_draft=False, bill_date__gt=month)
    monthly_billed_amount = client_bill_qs.aggregate(amount=Sum('billed_amount'))

    context = {
        'name': 'Muhammad Rizwan',
        'daily_earn': today_billed_amount.get("amount") or 0,
        'monthly_earn': monthly_billed_amount.get("amount") or 0,
        'daily_purchase': '3,000',
        'monthly_purchase': '50,000',
    }

    #shops = list(request.user.shop_set.values("id", "name"))
    #context["shops_list"] = shops
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
