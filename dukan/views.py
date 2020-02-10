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

@login_required(login_url='/login/')
def index(request):
    today = datetime.date.today()
    month = today.replace(day=1)

    client_bill_qs = ClientBill.objects.filter(is_draft=False, bill_time__gt=today)
    today_billed_amount = client_bill_qs.aggregate(amount=Sum('billed_amount'))

    client_bill_qs = ClientBill.objects.filter(is_draft=False, bill_time__gt=month)
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

class ShopListView(CustomLoginRequiredMixin, FilterView):
    model = Shop
    template_name = "shops/list.html"
    filterset_fields = ["name"]


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
