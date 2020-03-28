from django_filters.views import FilterView

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, UpdateView, DeleteView, DetailView

class CustomLoginRequiredMixin(LoginRequiredMixin):
    login_url = "/login"

class CustomListView(CustomLoginRequiredMixin, FilterView):
    shop_lookup = ""

    def get_context_data(self, **kwargs):
        context = super(CustomListView, self).get_context_data(**kwargs)
        object_list = context["object_list"]
        if self.shop_lookup:
            filter_kwargs = {self.shop_lookup: self.request.shop}
            object_list = object_list.filter(**filter_kwargs)
        context["object_list"] = object_list
        return context

class CustomViewMixin(object):
    def get_success_url(self):
        success_url = super(CustomViewMixin, self).get_success_url()
        return success_url+"/?"+self.request.GET.urlencode()

class CustomCreateView(CustomLoginRequiredMixin, CustomViewMixin, CreateView):
    pass

class CustomUpdateView(CustomLoginRequiredMixin, CustomViewMixin, UpdateView):
    pass

class CustomDeleteView(CustomLoginRequiredMixin, CustomViewMixin, DeleteView):
    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

class CustomDetailView(CustomLoginRequiredMixin, DetailView):
    pass
