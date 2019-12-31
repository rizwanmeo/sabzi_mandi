from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views


from dukan import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html', redirect_authenticated_user=True), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='login.html'), name='logout'),
    path('get_earn_data/', views.get_earn_data, name='get_earn_data'),
    path('get_top_client/', views.get_top_client, name='get_top_client'),
    path('suppliers/', views.get_suppliers, name='suppliers'),
    path('clients/', views.get_clients, name='clients'),
    path('admin/', admin.site.urls),
]
