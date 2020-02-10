from django.urls import re_path


from . import views

urlpatterns = [
    # supplier list view url
    re_path(r'^$', views.SupplierListView.as_view(), name='suppliers_list'),

    # supplier create view url
    re_path(r'^create/$', views.SupplierCreateView.as_view(), name='suppliers_create'),

    # supplier update view url
    re_path(r'^(?P<pk>\d+)/update/$', views.SupplierUpdateView.as_view(), name='^suppliers_update$'),
]
