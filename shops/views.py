from django.contrib import messages

from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required

from .models import *
from sabzi_mandi.views import *


class ShopListView(CustomListView):
    model = Shop
    template_name = "shops/list.html"
    filterset_fields = ["name"]


class ShopCreateView(CustomCreateView):
    model = Shop
    success_url = "/shops"
    template_name = "shops/form.html"
    fields = ["name", "phone", "address", "logo"]

    def form_valid(self, form):
        form.instance.owner = self.request.user
        super(ShopCreateView, self).form_valid(form)
        if form.instance.logo:
            form.instance.make_thumbnail()
        msg = 'Shop: [%s] was creates succfully.' % form.instance.name
        messages.add_message(self.request, messages.INFO, msg)
        return HttpResponseRedirect(self.get_success_url())

class ShopUpdateView(CustomUpdateView):
    model = Shop
    success_url = "/shops"
    template_name = "shops/form.html"
    fields = ["name", "phone", "address", "logo"]

    def form_valid(self, form):
        form.instance.last_modified = datetime.datetime.now()
        super(ShopUpdateView, self).form_valid(form)
        if form.instance.logo:
            form.instance.make_thumbnail()
        msg = 'Shop: [%s] was updated succfully.' % form.instance.name
        messages.add_message(self.request, messages.INFO, msg)
        return HttpResponseRedirect(self.get_success_url())


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
