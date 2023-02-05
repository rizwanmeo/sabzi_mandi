import datetime

from django.db.models import Max
from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, Http404, JsonResponse
from django.views.decorators.http import require_http_methods

from .forms import *
from .models import *
from .utils import *
from ledger.utils import *
from bills import supplier_utils
from sabzi_mandi.views import *
from clients.models import Client
from ledger.models import ClientLedgerEditable, SupplierLedgerEditable

class ClientBillListView(CustomListView):
    model = ClientBill
    template_name = "client_bills/list.html"
    filterset_fields = ["client", "bill_date"]
    shop_lookup = "client__shop"

    def get_context_data(self, **kwargs):
        context = super(ClientBillListView, self).get_context_data(**kwargs)

        object_list = context["object_list"]
        object_list = object_list.filter(is_draft=False)
        if self.request.GET.get("bill_date") is None:
            today = datetime.date.today().strftime("%Y-%m-%d")
            object_list = object_list.filter(bill_date=today)
        columns = ["id", "client__name", "client__identifier", "client__id", "created_time", "is_draft", "bill_date",
                   "balance", "billed_amount", "payment__amount", "billdetail__rate",
                   "billdetail__item__name", "billdetail__unit", "billdetail__item_count"]

        editable_bills = dict(ClientLedgerEditable.objects.filter(client__shop=self.request.shop).values_list("client_id", "tx_id"))

        data = {}
        vs = list(object_list.values(*columns))
        for row in vs:
            row_data = {}
            row_data["id"] = row["id"]
            row_data["pk"] = row["id"]
            row_data["client"] = {"name": row["client__name"], "identifier": row["client__identifier"], "id": row["client__id"]}
            row_data["created_time"] = row["created_time"]
            row_data["is_draft"] = row["is_draft"]
            row_data["bill_date"] = row["bill_date"]
            row_data["balance"] = row["balance"]
            row_data["billed_amount"] = row["billed_amount"]
            row_data["payment"] = {"amount": row["payment__amount"] or 0}
            row_data["total_items"] = 1
            row_data["billdetail"] = []

            row_data["previous_amount"] = row_data["balance"] - row["billed_amount"] + row_data["payment"]["amount"]
            detail = {}
            detail["item"] = {"name": row["billdetail__item__name"]}
            detail["rate"] = row["billdetail__rate"]
            detail["unit"] = "KG" if row["billdetail__unit"] == "k" else "Count"
            detail["item_count"] = row["billdetail__item_count"]

            row_data["billdetail"].append(detail)

            # Checking client payment can be edit or not
            client_id = row["client__id"]
            bill_tx_id = "bill-"+str(row["id"])
            if bill_tx_id == editable_bills.get(client_id, ""):
                row_data["editable"] = True

            try:
                data[row["id"]]["billdetail"].append(detail)
                data[row["id"]]["total_items"] += 1
            except KeyError:
                data[row["id"]] = row_data

        context["object_list"] = data.values()
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

def get_client_choices(form, shop_id):
    choices = [("", "Select a client for bill")]
    client_qs = form.fields["client"].queryset.filter(shop_id=shop_id)
    choices += list(client_qs.values_list("id", "name"))
    return choices

class ClientBillCreateView(CustomCreateView):
    model = ClientBill
    form_class = ClientBillForm
    success_url = "/bills/client"
    template_name = "client_bills/form.html"

    def form_valid(self, form):
        today = datetime.date.today()
        form.instance.is_draft = True
        payment_amount = form.cleaned_data.get("payment", 0)
        # Only create when payment amount > 0
        if payment_amount > 0:
            payment_obj = ClientPayment()
            payment_obj.client = form.instance.client
            payment_obj.payment_date = today
            payment_obj.amount = payment_amount
            payment_obj.is_draft = True
            payment_obj.save()
            form.instance.payment = payment_obj

        ClientBill.objects.filter(client=form.instance.client, is_draft=True).delete()
        super(ClientBillCreateView, self).form_valid(form)
        msg = 'Client: [%s] bill was added succfully. Please add bill detail'
        msg %= form.instance.client.name
        messages.add_message(self.request, messages.INFO, msg)
        obj = ClientBill.objects.get(client=form.instance.client, is_draft=True)
        success_url = "/bills/client/%d/detail-create/?" % self.object.pk
        success_url += self.request.GET.urlencode()
        return HttpResponseRedirect(success_url)

    def get_context_data(self, **kwargs):
        context = super(ClientBillCreateView, self).get_context_data(**kwargs)
        form = context["form"]
        form.fields["client"].widget.attrs["class"] = "fstdropdown-select"
        form.fields["client"].choices = get_client_choices(form, self.request.shop.id)

        if self.request.GET.get("client"):
            form.fields["client"].initial = self.request.GET.get("client")

        bill_date = datetime.date.today().strftime("%Y-%m-%d")
        if self.request.GET.get("bill_date"):
            bill_date = self.request.GET.get("bill_date")
        form.fields["bill_date"].initial = bill_date
        return context

class ClientBillUpdateView(CustomUpdateView):
    model = ClientBill
    form_class = ClientBillUpdateForm
    success_url = "/bills/client"
    template_name = "client_bills/form.html"

    def form_valid(self, form):
        super(ClientBillUpdateView, self).form_valid(form)
        update_ledger_date("bill-%d" % form.instance.pk, form.cleaned_data["bill_date"])
        msg = 'Client: [%s] bill was updated succfully.'
        msg %= form.instance.client.name
        messages.add_message(self.request, messages.INFO, msg)

        success_url = "/bills/client"
        return HttpResponseRedirect(success_url+"/?"+self.request.GET.urlencode())

    def get_context_data(self, **kwargs):
        context = super(ClientBillUpdateView, self).get_context_data(**kwargs)
        try:
            bill_tx_id = "bill-"+str(self.object.pk)
            ClientLedgerEditable.objects.get(tx_id=bill_tx_id)
        except:
            raise Http404

        form = context["form"]
        form.initial["bill_date"] = form.initial["bill_date"].strftime("%Y-%m-%d")
        return context

class ClientBillDeleteView(CustomDeleteView):
    model = ClientBill
    success_url = "/bills/client"

    def get_context_data(self, **kwargs):
        context = super(ClientBillDeleteView, self).get_context_data(**kwargs)
        if self.object.is_draft:
            return context

        try:
            bill_tx_id = "bill-"+str(self.object.pk)
            ClientLedgerEditable.objects.get(tx_id=bill_tx_id)
        except:
            raise Http404
        return context

    def delete(self, request, *args, **kwargs):
        super(ClientBillDeleteView, self).delete(request, *args, **kwargs)
        if not self.object.is_draft:
            bill_tx_id = "bill-"+str(self.object.pk)
            delete_ledger(bill_tx_id)
            self.object.client.current_balance -= self.object.billed_amount
            self.object.client.save()

        msg = 'Client: [%s] bill was delete succfully.' % self.object.client.name
        messages.add_message(self.request, messages.INFO, msg)
        return HttpResponseRedirect(self.get_success_url())

class ClientBillDetailDeleteView(CustomDeleteView):
    model = BillDetail
    success_url = "/bills/client"

    def delete(self, request, *args, **kwargs):
        if not self.get_object().bill.is_draft:
            raise Http404

        super(ClientBillDetailDeleteView, self).delete(request, *args, **kwargs)
        msg = 'Client bill: Item [%s] was delete succfully from bill.' % self.object.item.name
        messages.add_message(self.request, messages.INFO, msg)
        get_success_url = "/bills/client/%s/detail-create/?" % self.object.bill_id
        get_success_url += self.request.GET.urlencode()
        return HttpResponseRedirect(get_success_url)

class BillDetailCreateView(CustomCreateView):
    model = BillDetail
    template_name = "client_bills/bill_detail_form.html"
    fields = ["item", "unit", "rate", "item_count"]

    def get_success_url(self):
        return ""

    def form_valid(self, form):
        form.instance.bill = self.request.bill
        super(BillDetailCreateView, self).form_valid(form)
        msg = 'Client: [%s] bill detail was added succfully.' % self.request.bill.client.name
        success_url = "/bills/client/%d/detail-create/?shop_id=%d"
        return HttpResponseRedirect(success_url % (self.request.bill.pk, self.request.shop.pk))

    def get_context_data(self, **kwargs):
        context = super(BillDetailCreateView, self).get_context_data(**kwargs)
        form = context["form"]
        form.fields["item"].widget.attrs["class"] = "fstdropdown-select"
        form.fields["unit"].widget.attrs["class"] = "fstdropdown-select"
        form.fields["unit"].widget.attrs["data-searchdisable"] = "true"

        object_list = []
        billed_amount = 0
        qs = BillDetail.objects.filter(bill=self.request.bill)
        qs = qs.order_by("-id")
        vs = list(qs.values("id", "item__name", "unit", "rate", "item_count"))
        for row in vs:
            detail_obj = {}
            detail_obj["id"] = row["id"]
            detail_obj["name"] = row["item__name"]
            detail_obj["unit"] = "KG" if row["unit"] == 'k' else "Count"
            detail_obj["rate"] = row["rate"]
            detail_obj["item_count"] = row["item_count"]
            detail_obj["amount"] = row["rate"] * row["item_count"]
            billed_amount += detail_obj["amount"]
            object_list.append(detail_obj)

        # Load Item choices
        choices = []
        qs = Item.objects.all().order_by("id")
        vs = list(qs.values_list("id", "name"))
        form.fields["item"].choices = choices + vs
        form.fields["unit"].choices = form.fields["unit"].choices[1:]

        context["object_list"] = object_list
        context["billed_amount"] = billed_amount
        return context

    def get_bill_obj(self, bill_id):
        try:
            return ClientBill.objects.get(id=bill_id)
        except:
            raise Http404

    def get(self, request, *args, **kwargs):
        request.bill = self.get_bill_obj(kwargs.get("bill_id", 0))
        return super(BillDetailCreateView, self).get(request)

    def post(self, request, *args, **kwargs):
        request.bill = self.get_bill_obj(kwargs.get("bill_id", 0))
        return super(BillDetailCreateView, self).post(request)


@login_required(login_url='/login/')
@require_http_methods(["GET"])
def print_bill(request, client_id):
    try:
        client_obj = Client.objects.get(id=int(client_id))
    except:
        raise Http404

    if 'bill_date' in request.GET:
        date = request.GET['bill_date']
    else:
        date = ''

    context = get_bill_data(request, client_obj, date)
    context["logo_path"] = client_obj.shop.logo.url
    return render(request, 'client_bills/print.html', context)

@login_required(login_url='/login/')
@require_http_methods(["POST"])
def done_bill(request, bill_id):
    try:
        bill_obj = ClientBill.objects.get(id=int(bill_id), is_draft=True)
    except:
        raise Http404

    if bill_obj.billdetail_set.count() == 0:
        raise Http404

    action = int(request.POST.get("submit", 0))
    if action == 1:
        done_drafted_bill(request, bill_obj)
        redirect_url = "/bills/client/?"+request.GET.urlencode()
        msg = 'Client: [%s] Bill was done succfully.' % bill_obj.client.name
        messages.add_message(request, messages.INFO, msg)
        return HttpResponseRedirect(redirect_url)
    elif action == 2:
        done_drafted_bill(request, bill_obj)
        context = get_print_bill_data(request, bill_obj)
        return render(request, 'client_bills/print.html', context)
    elif action == 3:
        done_drafted_bill(request, bill_obj)
        redirect_url = "/bills/client/create/?"
        redirect_url += request.GET.urlencode()
        msg = 'Client: [%s] Bill was done succfully.' % bill_obj.client.name
        messages.add_message(request, messages.INFO, msg)
        return HttpResponseRedirect(redirect_url)
    else:
        raise Http404

def get_supplier_choices(form, shop_id):
    choices = [("", "Select a supplier for bill")]
    supplier_qs = form.fields["supplier"].queryset.filter(shop_id=shop_id)
    choices += list(supplier_qs.values_list("id", "name"))
    return choices

class SupplierBillListView(CustomListView):
    model = SupplierBill
    template_name = "bills/supplier/list.html"
    filterset_fields = ["supplier", "bill_date"]
    shop_lookup = "supplier__shop"

    def get_context_data(self, **kwargs):
        context = super(SupplierBillListView, self).get_context_data(**kwargs)

        object_list = context["object_list"]
        object_list = object_list.filter(is_draft=False)
        if self.request.GET.get("bill_date") is None:
            today = datetime.date.today().strftime("%Y-%m-%d")
            object_list = object_list.filter(bill_date=today)
        columns = ["id", "supplier__name", "supplier__identifier", "supplier__id", "created_time", "is_draft", "bill_date",
                   "balance", "billed_amount", "other_expence", "supplierbilldetail__rate",
                   "supplierbilldetail__item__name", "supplierbilldetail__unit", "supplierbilldetail__item_count"]

        editable_bills = dict(SupplierLedgerEditable.objects.filter(supplier__shop=self.request.shop).values_list("supplier_id", "tx_id"))

        data = {}
        vs = list(object_list.values(*columns))
        for row in vs:
            row_data = {}
            row_data["id"] = row["id"]
            row_data["pk"] = row["id"]
            row_data["supplier"] = {"name": row["supplier__name"], "identifier": row["supplier__identifier"], "id": row["supplier__id"]}
            row_data["created_time"] = row["created_time"]
            row_data["is_draft"] = row["is_draft"]
            row_data["bill_date"] = row["bill_date"]
            row_data["balance"] = row["balance"]
            row_data["billed_amount"] = row["billed_amount"]
            row_data["total_items"] = 1
            row_data["billdetail"] = []

            row_data["previous_amount"] = row_data["balance"] - row["billed_amount"]
            detail = {}
            detail["item"] = {"name": row["supplierbilldetail__item__name"]}
            detail["rate"] = row["supplierbilldetail__rate"]
            detail["unit"] = "KG" if row["supplierbilldetail__unit"] == "k" else "Count"
            detail["item_count"] = row["supplierbilldetail__item_count"]

            row_data["billdetail"].append(detail)
            # Checking supplier payment can be edit or not
            supplier_id = row["supplier__id"]
            bill_tx_id = "bill-"+str(row["id"])
            if bill_tx_id == editable_bills.get(supplier_id, "") or row["other_expence"].get("is_cash") == "y":
                row_data["editable"] = True

            try:
                data[row["id"]]["billdetail"].append(detail)
                data[row["id"]]["total_items"] += 1
            except KeyError:
                data[row["id"]] = row_data

        context["object_list"] = data.values()
        supplier_id = self.request.GET.get("supplier", "")
        supplier_id = int(supplier_id) if supplier_id.isdigit() else 0
        qs = Supplier.objects.filter(shop=self.request.shop)
        context["supplier_list"] = list(qs.values("id", "name"))
        context["selected_supplier"] = supplier_id
        supplier_id = self.request.GET.get("supplier", "")

        selected_date = self.request.GET.get("bill_date", "")
        if selected_date == "":
            selected_date = datetime.date.today().strftime("%Y-%m-%d")
        context["selected_date"] = selected_date

        return context


class SupplierBillCreateView(CustomCreateView):
    model = SupplierBill
    success_url = "/bills/supplier"
    form_class = SupplierBillForm
    template_name = "bills/supplier/form.html"

    def form_valid(self, form):
        data = {}
        super(SupplierBillCreateView, self).form_valid(form)
        if form.data["farmer_name"] != "":
            data["farmer_name"] = form.data["farmer_name"]
        if form.data["commission_amount"] != "":
            data["commission_amount"] = form.data["commission_amount"]
        if form.data["unloading_cost"] != "":
            data["unloading_cost"] = form.data["unloading_cost"]
        if form.data["vahicle_rent"] != "":
            data["vahicle_rent"] = form.data["vahicle_rent"]
        if form.data["farmer_wages"] != "":
            data["farmer_wages"] = form.data["farmer_wages"]
        if form.data["labour_cost"] != "":
            data["labour_cost"] = form.data["labour_cost"]
        if form.data["begs_amount"] != "":
            data["begs_amount"] = form.data["begs_amount"]
        if form.data["market_tax"] != "":
            data["market_tax"] = form.data["market_tax"]
        if form.data["beg_rope"] != "":
            data["beg_rope"] = form.data["beg_rope"]
        if form.data["cash_amount"] != "":
            data["cash_amount"] = form.data["cash_amount"]

        data["is_cash"] = form.data["is_cash"]
        form.instance.other_expence = data
        form.instance.is_draft = True
        form.instance.save()

        msg = 'Supplier: bill was created succfully.'
        messages.add_message(self.request, messages.INFO, msg)
        self.success_url = "/bills/supplier/"+str(form.instance.pk)
        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super(SupplierBillCreateView, self).get_context_data(**kwargs)
        form = context["form"]
        form.fields["supplier"].widget.attrs["class"] = "fstdropdown-select"
        form.fields["supplier"].choices = get_supplier_choices(form, self.request.shop.id)

        if self.request.GET.get("supplier"):
            form.fields["supplier"].initial = self.request.GET.get("supplier")

        bill_date = datetime.date.today()
        if self.request.GET.get("bill_date"):
            bill_date = datetime.datetime.strptime(self.request.GET.get("bill_date"), '%Y-%m-%d').date()

        form.fields["bill_date"].initial = bill_date
        form.fields["unloading_cost"].initial = 20
        form.fields["commission_amount"].initial = 10

        context["bill_detail_form"] = SupplierBillDetailForm()
        return context


class SupplierBillDeleteView(CustomDeleteView):
    model = SupplierBill
    success_url = "/bills/supplier"

    def get_context_data(self, **kwargs):
        context = super(SupplierBillDeleteView, self).get_context_data(**kwargs)
        if self.object.is_draft:
            return context

        try:
            if self.object.other_expence.get("is_cash") == "n":
                bill_tx_id = "bill-"+str(self.object.pk)
                SupplierLedgerEditable.objects.get(tx_id=bill_tx_id)
        except:
            raise Http404
        return context

    def delete(self, request, *args, **kwargs):
        super(SupplierBillDeleteView, self).delete(request, *args, **kwargs)
        if not self.object.is_draft:
            bill_tx_id = "bill-"+str(self.object.pk)
            if self.object.other_expence.get("is_cash") == "n":
                delete_supplier_ledger(bill_tx_id)
                self.object.supplier.current_balance -= self.object.billed_amount
                self.object.supplier.save()

        msg = 'Supplier: [%s] bill was delete succfully.' % self.object.supplier.name
        messages.add_message(self.request, messages.INFO, msg)
        return HttpResponseRedirect(self.get_success_url())


class SupplierBillDetailDeleteView(CustomDeleteView):
    model = SupplierBillDetail
    success_url = "/bills/supplier"

    def delete(self, request, *args, **kwargs):
        if not self.get_object().bill.is_draft:
            raise Http404

        super(SupplierBillDetailDeleteView, self).delete(request, *args, **kwargs)
        msg = 'Supplier bill: Item [%s] was delete succfully from bill.' % self.object.item.name
        messages.add_message(self.request, messages.INFO, msg)
        get_success_url = "/bills/supplier/%s/?" % self.object.bill_id
        get_success_url += self.request.GET.urlencode()
        return HttpResponseRedirect(get_success_url)

class SupplierBillUpdateView(CustomUpdateView):
    model = SupplierBill
    success_url = "/bills/supplier"
    form_class = SupplierBillForm
    detail_form = None
    template_name = "bills/supplier/form.html"

    def get_context_data(self, **kwargs):
        context = super(SupplierBillUpdateView, self).get_context_data(**kwargs)

        form = context["form"]
        form.fields["supplier"].widget.attrs["class"] = "fstdropdown-select"
        form.fields["supplier"].choices = get_supplier_choices(form, self.request.shop.id)
        form.fields["supplier"].initial = form.instance.supplier.id
        form.fields["bill_date"].initial = form.instance.bill_date

        if "farmer_name" in self.object.other_expence:
            form.fields["farmer_name"].initial = self.object.other_expence["farmer_name"]
        if "commission_amount" in self.object.other_expence:
            form.fields["commission_amount"].initial = self.object.other_expence["commission_amount"]
        else:
            form.fields["commission_amount"].initial = 10

        if "unloading_cost" in self.object.other_expence:
            form.fields["unloading_cost"].initial = self.object.other_expence["unloading_cost"]
        else:
            form.fields["unloading_cost"].initial = 20

        if "vahicle_rent" in self.object.other_expence:
            form.fields["vahicle_rent"].initial = self.object.other_expence["vahicle_rent"]
        if "farmer_wages" in self.object.other_expence:
            form.fields["farmer_wages"].initial = self.object.other_expence["farmer_wages"]
        if "labour_cost" in self.object.other_expence:
            form.fields["labour_cost"].initial = self.object.other_expence["labour_cost"]
        if "begs_amount" in self.object.other_expence:
            form.fields["begs_amount"].initial = self.object.other_expence["begs_amount"]
        if "market_tax" in self.object.other_expence:
            form.fields["market_tax"].initial = self.object.other_expence["market_tax"]
        if "beg_rope" in self.object.other_expence:
            form.fields["beg_rope"].initial = self.object.other_expence["beg_rope"]
        if "cash_amount" in self.object.other_expence:
            form.fields["cash_amount"].initial = self.object.other_expence["cash_amount"]
        if "is_cash" in self.object.other_expence:
            form.fields["is_cash"].initial = self.object.other_expence["is_cash"]

        context["object"] = self.object
        if self.detail_form is not None:
            context["bill_detail_form"] = self.detail_form
        else:
            context["bill_detail_form"] = SupplierBillDetailForm()

        item_count = 0
        total_amount = 0
        context["object_list"] = []
        vs = list(self.object.supplierbilldetail_set.values("id", "item__name", "unit", "rate", "weight", "item_count"))
        for row in vs:
            detail= {}
            detail["id"] = row["id"]
            detail["name"] = row["item__name"]
            detail["rate"] = row["rate"]
            detail["item_count"] = row["item_count"]
            detail["weight"] = row["weight"] or "-"
            if row["unit"] == "k":
                detail["unit"] = "KG"
                detail["amount"] = (row["weight"] if "weight" in row else row["item_count"]) * row["rate"]
            else:
                detail["unit"] = "Count"
                detail["amount"] = row["item_count"] * row["rate"]

            context["object_list"].append(detail)
            item_count += detail["item_count"]
            total_amount += detail["amount"]


        total_expense = 0
        remaining_amount = 0
        unloading_amount = ""
        commission_amount = ""
        final_amount = total_amount
        if final_amount > 0:
            if "commission_amount" in self.object.other_expence:
                commission_amount = supplier_utils.percentage(self.object.other_expence["commission_amount"], total_amount)
                final_amount -= commission_amount

            if "unloading_cost" in self.object.other_expence:
                unloading_amount = float(self.object.other_expence["unloading_cost"])*item_count
                final_amount -= unloading_amount

        context["billed_amount"] = final_amount

        if "vahicle_rent" in self.object.other_expence:
            total_expense += float(self.object.other_expence["vahicle_rent"])
        if "farmer_wages" in self.object.other_expence:
            total_expense += float(self.object.other_expence["farmer_wages"])
        if "labour_cost" in self.object.other_expence:
            total_expense += float(self.object.other_expence["labour_cost"])
        if "begs_amount" in self.object.other_expence:
            total_expense += float(self.object.other_expence["begs_amount"])
        if "market_tax" in self.object.other_expence:
            total_expense += float(self.object.other_expence["market_tax"])
        if "beg_rope" in self.object.other_expence:
            total_expense += float(self.object.other_expence["beg_rope"])

        final_amount -= total_expense
        if "cash_amount" in self.object.other_expence:
            remaining_amount = final_amount - float(self.object.other_expence["cash_amount"])
        else:
            remaining_amount = final_amount

        context["total_expense"] = total_expense
        context["commission_amount"] = commission_amount
        context["unloading_amount"] = unloading_amount
        context["total_amount"] = total_amount
        context["final_amount"] = final_amount
        context["remaining_amount"] = remaining_amount

        return context

    def post(self, request, *args, **kwargs):
        if request.method =='POST' and 'update_bill' in request.POST:
            return super(SupplierBillUpdateView, self).post(request, *args, **kwargs)
        else:
            self.object = self.get_object()
            self.success_url = "/bills/supplier/"+str(self.object.pk)
            return HttpResponseRedirect(self.get_success_url())

    def form_valid(self, form):
        data = {}
        super(SupplierBillUpdateView, self).form_valid(form)
        if form.data["farmer_name"] != "":
            data["farmer_name"] = form.data["farmer_name"]
        if form.data["commission_amount"] != "":
            data["commission_amount"] = form.data["commission_amount"]
        if form.data["unloading_cost"] != "":
            data["unloading_cost"] = form.data["unloading_cost"]
        if form.data["vahicle_rent"] != "":
            data["vahicle_rent"] = form.data["vahicle_rent"]
        if form.data["farmer_wages"] != "":
            data["farmer_wages"] = form.data["farmer_wages"]
        if form.data["labour_cost"] != "":
            data["labour_cost"] = form.data["labour_cost"]
        if form.data["begs_amount"] != "":
            data["begs_amount"] = form.data["begs_amount"]
        if form.data["market_tax"] != "":
            data["market_tax"] = form.data["market_tax"]
        if form.data["beg_rope"] != "":
            data["beg_rope"] = form.data["beg_rope"]
        if form.data["cash_amount"] != "":
            data["cash_amount"] = form.data["cash_amount"]

        data["is_cash"] = form.data["is_cash"]
        form.instance.other_expence = data
        form.instance.save()
        msg = 'Supplier: bill was update succfully.'
        messages.add_message(self.request, messages.INFO, msg)
        self.success_url = "/bills/supplier/"+str(self.object.pk)
        return HttpResponseRedirect(self.get_success_url())

@login_required(login_url='/login/')
def add_supplier_bill_detail(request, bill_id=None):
    if bill_id is not None:
        try:
            bill_obj = SupplierBill.objects.get(id=int(bill_id))
        except:
            redirect_url = "/bills/supplier/"+bill_id+"/?"+request.GET.urlencode()
            msg = 'Supplier bill: Invalid bill id OR you cannot add items in this bill.'
            messages.add_message(request, messages.ERROR, msg)
            return HttpResponseRedirect(redirect_url)
    else:
        return SupplierBillCreateView.as_view()(request)

    if request.method =='POST' and 'add_detail' in request.POST:
        form = SupplierBillDetailForm(request.POST)
        if form.is_valid():
            form.instance.bill = bill_obj
            form.save()
            msg = 'Supplier: bill detail was update succfully.'
            messages.add_message(request, messages.INFO, msg)
        else:
            msg = 'Supplier: bill detail was update succfully.'
            messages.add_message(request, messages.ERROR, msg)
            SupplierBillUpdateView.detail_form = form

    if request.method =='GET':
        form = SupplierBillDetailForm()
        SupplierBillUpdateView.detail_form = form

    return SupplierBillUpdateView.as_view()(request, pk=bill_id)

@login_required(login_url='/login/')
@require_http_methods(["POST"])
def done_supplier_bill(request, pk):
    try:
        bill_obj = SupplierBill.objects.get(id=int(pk), is_draft=True)
    except Exception as e:
        redirect_url = "/bills/supplier/"+pk+"/?"+request.GET.urlencode()
        msg = 'Supplier bill: Invalid bill id' + str(e)
        messages.add_message(request, messages.ERROR, msg)
        return HttpResponseRedirect(redirect_url)

    if bill_obj.supplierbilldetail_set.count() == 0:
        redirect_url = "/bills/supplier/"+pk+"/?"+request.GET.urlencode()
        msg = 'Supplier bill: There was no detail in bill.'
        messages.add_message(request, messages.ERROR, msg)
        return HttpResponseRedirect(redirect_url)

    action = int(request.POST.get("submit", 0))
    if action == 1:
        supplier_utils.done_drafted_bill(request, bill_obj)
        redirect_url = "/bills/supplier/?"+request.GET.urlencode()
        msg = 'Supplier: [%s] Bill was done succfully.' % bill_obj.supplier.name
        messages.add_message(request, messages.INFO, msg)
        return HttpResponseRedirect(redirect_url)
    elif action == 2:
        supplier_utils.done_drafted_bill(request, bill_obj)
        redirect_url = "/bills/supplier/%d/print/?" % bill_obj.pk
        redirect_url += request.GET.urlencode()
        return HttpResponseRedirect(redirect_url)
    elif action == 3:
        supplier_utils.done_drafted_bill(request, bill_obj)
        redirect_url = "/bills/supplier/create/?"+request.GET.urlencode()
        msg = 'Supplier: [%s] Bill was done succfully.' % bill_obj.supplier.name
        messages.add_message(request, messages.INFO, msg)
        return HttpResponseRedirect(redirect_url)
    else:
        raise Http404

@login_required(login_url='/login/')
@require_http_methods(["GET"])
def print_supplier_bill(request, pk):
    try:
        bill_obj = SupplierBill.objects.get(id=int(pk), is_draft=False)
    except Exception as e:
        msg = 'Supplier bill: Invalid bill id' + str(e)
        messages.add_message(request, messages.ERROR, msg)
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    context = supplier_utils.get_print_bill_data(request, bill_obj)
    return render(request, 'bills/supplier/print.html', context)

class SupplierDailyBillReport(CustomListView):
    model = SupplierBill
    filterset_fields = ["supplier", "bill_date"]
    template_name = "bills/supplier/daily_detail.html"

    def get_context_data(self, **kwargs):
        context = super(SupplierDailyBillReport, self).get_context_data(**kwargs)
        bill_date = self.request.GET.get("bill_date", "")
        if bool(bill_date):
            bill_date = datetime.datetime.strptime(bill_date, "%Y-%m-%d").date()
        else:
            bill_date = datetime.date.today()

        context["bill_date"] = bill_date.strftime("%Y-%m-%d")
        return supplier_utils.get_supplier_daily_detail(self.request, context)

class SupplierDailyBillReportPrint(CustomListView):
    model = SupplierBill
    filterset_fields = ["supplier", "bill_date"]
    template_name = "bills/supplier/daily_detail-print.html"

    def get_context_data(self, **kwargs):
        context = super(SupplierDailyBillReportPrint, self).get_context_data(**kwargs)
        context["logo_path"] = self.request.shop.logo.url
        return supplier_utils.get_supplier_daily_detail(self.request, context)

class SupplierBillCashUpdateView(CustomUpdateView):
    model = SupplierBill
    form_class = SupplierBillCashForm
    success_url = "/bills/supplier/daily-detail"
    template_name = "bills/supplier/bill-cash-form.html"
