from django.urls import re_path

from . import views

urlpatterns = [
    # all other urls
    re_path(r'^get_earn_data/$', views.get_earn_data, name='get_earn_data'),
    re_path(r'^get_top_client/$', views.get_top_client, name='get_top_client'),
]
