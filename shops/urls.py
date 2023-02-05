from django.urls import re_path

from . import views

urlpatterns = [
    # all list view urls
    re_path(r'^$', views.ShopListView.as_view(), name='shops_list'),

    # all create view urls
    re_path(r'^create/$', views.ShopCreateView.as_view(), name='shops_create'),
    re_path(r'^make-default/$', views.make_default_shop, name='make-default'),

    # all create view urls
    re_path(r'^cashbook/$', views.shop_cashbook_view, name='shops_cashbook'),
    # all update view urls
    re_path(r'^cashbook/create/$', views.ShopCashbookCreateView.as_view(), name='shops_cashbook_create'),
    # all update view urls
    re_path(r'^cashbook/(?P<pk>\d+)/update/$', views.ShopCashbookUpdateView.as_view(), name='^shops_cashbook_update'),

    # all update view urls
    re_path(r'^(?P<pk>\d+)/update/$', views.ShopUpdateView.as_view(), name='^shops_update'),
]
