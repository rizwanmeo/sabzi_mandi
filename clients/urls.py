from django.urls import re_path

from . import views


urlpatterns = [
    # client list view url
    re_path(r'^$', views.ClientListView.as_view(), name='clients_list'),

    # client create view url
    re_path(r'^create/$', views.ClientCreateView.as_view(), name='clients_create'),

    # client update view url
    re_path(r'^(?P<pk>\d+)/update/$', views.ClientUpdateView.as_view(), name='^clients_update$'),
]
