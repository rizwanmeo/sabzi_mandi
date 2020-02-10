from django.urls import re_path

from . import views

urlpatterns = [
    # all list view urls
    re_path(r'^$', views.ShopListView.as_view(), name='shops_list'),

    # all create view urls
    re_path(r'^create/$', views.ShopCreateView.as_view(), name='shops_create'),
    re_path(r'^make-default/$', views.make_default_shop, name='make-default$'),

    # all update view urls
    re_path(r'^(?P<pk>\d+)/update/$', views.ShopUpdateView.as_view(), name='^shops_update$'),
]
