from django.urls import re_path

from . import views


urlpatterns = [
    # client list view url
    re_path(r'^$', views.ClientListView.as_view(), name='clients_list'),

    # client create view url
    re_path(r'^create/$', views.ClientCreateView.as_view(), name='clients_create'),

    # client update view url
    re_path(r'^(?P<pk>\d+)/update/$', views.ClientUpdateView.as_view(), name='clients_update'),

    # client detail view url
    re_path(r'^(?P<pk>\d+)/detail/$', views.ClientDetailView.as_view(), name='clients_detail'),
    re_path(r'^(?P<pk>\d+)/print/$', views.ClientDetailPrintView.as_view(), name='clients_detail_print'),

    # client delete view url
    re_path(r'^(?P<pk>\d+)/delete/$', views.ClientDeleteView.as_view(), name='clients_delete'),
]
