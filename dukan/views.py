from django.db.models import Sum, Count
from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, Http404, JsonResponse
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from dukan.models import *
from dukan.forms import BillDetailForm

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

    def get_context_data(self):
        context = super(SupplierListView, self).get_context_data()
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

class ClientListView(CustomLoginRequiredMixin, ListView):
    model = Client
    template_name = "clients/list.html"

    def get_context_data(self):
        context = super(ClientListView, self).get_context_data()
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

class ClientBillListView(CustomLoginRequiredMixin, ListView):
    model = ClientBill
    template_name = "client_bills/list.html"

    def get_context_data(self):
        context = super(ClientBillListView, self).get_context_data()
        object_list = context["object_list"]
        object_list = object_list.filter(client__shop=self.request.shop)
        object_list = object_list.annotate(items=Count('billdetail__item'))
        context["object_list"] = object_list
        return context


class ClientBillCreateView(CustomLoginRequiredMixin, CreateView):
    model = ClientBill
    success_url = "/client-bills"
    template_name = "client_bills/form.html"
    fields = ["client"]

    def form_valid(self, form):
        super(ClientBillCreateView, self).form_valid(form)
        msg = 'Client: [%s] was created succfully.' % form.instance.name
        messages.add_message(self.request, messages.INFO, msg)
        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super(ClientBillCreateView, self).get_context_data(**kwargs)
        form = context["form"]
        choices = [("", "Select a client for bill")]
        form.fields["client"].widget.attrs["class"] = "fstdropdown-select"
        form.fields["client"].widget.attrs["onChange"] = "onchangeEvent();"
        form.fields["client"].widget.attrs["required"] = False
        client_qs = form.fields["client"].queryset.filter(shop=self.request.shop)
        choices += list(client_qs.values_list("id", "name"))
        form.fields["client"].choices = choices
        context["detail_form"] = BillDetailForm()
        return context


class ClientBillDeleteView(CustomLoginRequiredMixin, DeleteView):
    model = ClientBill
    success_url = "/client-bills"

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        if not self.get_object().is_draft:
            raise Http404
        super(ClientBillDeleteView, self).delete(request, *args, **kwargs)
        msg = 'Client: [%s] bill was delete succfully.' % self.object.client.name
        messages.add_message(self.request, messages.INFO, msg)
        return HttpResponseRedirect(self.get_success_url())

class ClientBillUpdateView(CustomLoginRequiredMixin, UpdateView):
    model = ClientBill
    success_url = "/client-bills"
    template_name = "client_bills/form.html"
    fields = ["client"]

    def form_valid(self, form):
        form.instance.bill_time = datetime.datetime.now()
        super(ClientUpdateView, self).form_valid(form)
        msg = 'Client: [%s] was updated succfully.' % form.instance.name
        messages.add_message(self.request, messages.INFO, msg)
        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super(ClientBillUpdateView, self).get_context_data(**kwargs)
        form = context["form"]
        choices = [("", "Select a client for bill")]
        form.fields["client"].widget.attrs["class"] = "fstdropdown-select"
        form.fields["client"].widget.attrs["required"] = False
        client_qs = form.fields["client"].queryset.filter(shop__owner=self.request.user)
        choices += list(client_qs.values_list("id", "name"))
        form.fields["client"].choices = choices
        context["detail_list"] = self.object.billdetail_set.all()
        context["detail_form"] = BillDetailForm()
        context["current_balance"] = int(self.object.client.current_balance)
        context["billed_amount"] = 0
        billdetail_vs = list(self.object.billdetail_set.values("rate", "item_count"))
        for detail_obj in billdetail_vs:
            context["billed_amount"] += detail_obj["rate"] * detail_obj["item_count"]
        context["billed_amount"] = int(context["billed_amount"])

        return context

@login_required(login_url='/login/')
def client_bill_detail(request, client_id, bill_id=0):
    client_obj = Client.objects.get(id=client_id, shop=request.shop)
    if request.method == "POST":
        form = BillDetailForm(request.POST)
        if form.is_valid():
            try:
                if int(bill_id) > 0:
                    bill_obj = ClientBill.objects.get(id=bill_id, client_id=client_id)
                else:
                    bill_obj = ClientBill.objects.annotate(item_count=Count('billdetail')).get(client_id=client_id, is_draft=True, item_count=0)
                    bill_id = bill_obj.id
            except ClientBill.DoesNotExist:
                bill_obj = ClientBill(client=client_obj, is_draft=True)
                bill_obj.save()
                bill_id = bill_obj.id

            form.instance.bill = bill_obj
            form.save()
            data = {"id": form.instance.id, "unit": form.instance.get_unit_display(),
                    "rate": form.instance.rate, "item": form.instance.item.name,
                    "item_count": form.instance.item_count}
            return JsonResponse({"status": True, "data": data, "bill_id": bill_id})
        else:
            return JsonResponse({"status": False, "errors": form.errors})
    return JsonResponse({"status": False, "description": "Invalid request"})

@login_required(login_url='/login/')
def get_drafted_bill(request, client_id):
    data = {}
    draft_bills = []
    if request.method == "GET":
        client = Client.objects.get(id=client_id)
        kwargs = {
            "client_id":      client_id,
            "client__shop":   request.shop,
            "is_draft":       True}
        client_qs = ClientBill.objects.filter(**kwargs).order_by("-created_time")
        for obj in client_qs[:10]:
            draft_bill = {}
            billdetail_vs = list(obj.billdetail_set.values("rate", "item_count"))
            item_count = len(billdetail_vs)
            if item_count == 0: continue
            draft_bill["bill_id"] = obj.id
            draft_bill["billed_amount"] = 0
            draft_bill["item_count"] = item_count
            draft_bill["created_time"] = obj.created_time.strftime("%d %b, %Y %I:%M%p")
            for detail_obj in billdetail_vs:
                draft_bill["billed_amount"] += detail_obj["rate"] * detail_obj["item_count"]
            draft_bills.append(draft_bill)
        data["draft_bills"] = draft_bills
        data["balance"] = client.current_balance

    return JsonResponse({"status": True, "data": data})

@login_required(login_url='/login/')
def done_drafted_bill(request, client_id, bill_id):
    if request.method == "POST":
        billed_amount = 0
        bill_obj = ClientBill.objects.get(id=int(bill_id), is_draft=True)
        billdetail_vs = bill_obj.billdetail_set.values("rate", "item_count")
        for detail_obj in billdetail_vs:
            billed_amount += detail_obj["rate"] * detail_obj["item_count"]
        bill_obj.is_draft = False
        bill_obj.client_id = client_id
        bill_obj.billed_amount = billed_amount
        bill_obj.bill_time = datetime.datetime.now()
        bill_obj.client.current_balance -= billed_amount
        bill_obj.balance = bill_obj.client.current_balance
        bill_obj.client.save()
        bill_obj.save()
        msg = 'Client: [%s] Bill was done succfully.' % bill_obj.client.name
        messages.add_message(request, messages.INFO, msg)
        return JsonResponse({"status": True, "description": "Successfully done"})
    else:
        return JsonResponse({"status": False, "description": "Invalid request"})

@login_required(login_url='/login/')
def print_bill(request, bill_id):
    context = {}
    if request.method == "GET":
        obj = ClientBill.objects.get(id=int(bill_id), is_draft=False)
        context["obj"] = obj

    return render(request, 'client_bills/print.html', context)

@login_required(login_url='/login/')
def delete_client_bill_detail(request, detail_id):
    if request.method == "DELETE":
        try:
            obj = BillDetail.object.get(id=detail_id)
            obj.delete()
            return JsonResponse({"status": True, "description": "Successfully deleted"})
        except:
            return JsonResponse({"status": False, "description": "Invalid bill ID"})
    return JsonResponse({"status": False, "description": "Invalid Request"})

@login_required(login_url='/login/')
def ledger_print(request):
    context = {}
    if request.method == "GET":
        today = datetime.date.today()
        filter_kwargs = {
            "client__shop": request.shop,
            "is_draft": False,
            #"bill_time__gt": today,
        }

        data = {}
        client_bill_qs = ClientBill.objects.filter(**filter_kwargs)
        columns = ['client__name', 'client__id', 'client__current_balance', 'billed_amount']
        client_bill_vs = client_bill_qs.values(*columns)
        for obj in client_bill_vs:
            pk = obj["client__id"]
            name = obj["client__name"]
            amount = obj["billed_amount"]
            balance = obj["client__current_balance"]
            try:
                data[pk]["amount"] += amount
                data[pk]["balance"] = data[pk]["balance"]+amount
            except:
                data[pk] = {"id": pk, 
                            "name": name, 
                            "amount": amount, 
                            "balance": balance+amount,
                            "total": balance}
        vs = list(data.values())
        ledger_list1, ledger_list2 = vs[:int(len(vs)/2)], vs[int(len(vs)/2):]
        context["ledger_list1"] = ledger_list1
        context["ledger_list2"] = ledger_list2[:-1]

    return render(request, 'ledger/print.html', context)

@login_required(login_url='/login/')
def ledger_view(request):
    context = {}
    if request.method == "GET":
        today = datetime.date.today()
        filter_kwargs = {
            "client__shop": request.shop,
            "is_draft": False,
            #"bill_time__gt": today,
        }

        data = {}
        client_bill_qs = ClientBill.objects.filter(**filter_kwargs)
        columns = ['client__name', 'client__id', 'client__current_balance', 'billed_amount']
        client_bill_vs = client_bill_qs.values(*columns)
        for obj in client_bill_vs:
            pk = obj["client__id"]
            name = obj["client__name"]
            amount = obj["billed_amount"]
            balance = obj["client__current_balance"]
            try:
                data[pk]["amount"] += amount
                data[pk]["balance"] = data[pk]["balance"]+amount
            except:
                data[pk] = {"id": pk, 
                            "name": name, 
                            "amount": amount, 
                            "balance": balance+amount,
                            "total": balance}
        vs = list(data.values())
        context["ledger_list"] = vs

    return render(request, 'ledger/list.html', context)

