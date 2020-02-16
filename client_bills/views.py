import datetime

from django.db.models import Sum, Count
from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, Http404, JsonResponse
from django.views.generic import CreateView, UpdateView, DeleteView

from .models import *
from .forms import BillDetailForm
from clients.models import Client

from django_filters.views import FilterView
from sabzi_mandi.views import CustomLoginRequiredMixin

class ClientBillListView(CustomLoginRequiredMixin, FilterView):
    model = ClientBill
    template_name = "client_bills/list.html"
    filterset_fields = ["client", "client__name"]

    def get_context_data(self, **kwargs):
        context = super(ClientBillListView, self).get_context_data(**kwargs)
        object_list = context["object_list"]
        object_list = object_list.filter(client__shop=self.request.shop)
        object_list = object_list.annotate(items=Count('billdetail__item'))
        context["object_list"] = object_list
        client_id = self.request.GET.get("client", "")
        client_id=int(client_id) if client_id.isdigit() else 0
        qs = Client.objects.filter(shop=self.request.shop)
        context["client_list"] = list(qs.values("id", "name"))
        context["selected_client"] = client_id
        client_id = self.request.GET.get("client", "")

        selected_date = self.request.GET.get("bill_date", "")
        if selected_date == "":
            selected_date = datetime.date.today().strftime("%Y-%m-%d")
        context["selected_date"] = selected_date
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
        context["bill_detail_list"] = obj.billdetail_set.all()

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

