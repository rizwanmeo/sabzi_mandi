from django_filters.views import FilterView

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, UpdateView, DeleteView

class CustomLoginRequiredMixin(LoginRequiredMixin):
    login_url = "/login"

class CustomListView(CustomLoginRequiredMixin, FilterView):
    pass

class CustomViewMixin(object):
    def get_success_url(self):
        success_url = super(CustomViewMixin, self).get_success_url()
        return success_url+"/?"+self.request.GET.urlencode()

class CustomCreateView(CustomLoginRequiredMixin, CustomViewMixin, CreateView):
    pass

class CustomUpdateView(CustomLoginRequiredMixin, CustomViewMixin, UpdateView):
    pass

class CustomDeleteView(CustomLoginRequiredMixin, CustomViewMixin, DeleteView):
    pass
