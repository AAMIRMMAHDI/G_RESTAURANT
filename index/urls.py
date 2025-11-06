from django.urls import path
from . import views

app_name = 'index'

urlpatterns = [
    path('', views.home, name='home'),
    path('order/', views.order_menu, name='order_menu'),
    path('sync-cart/', views.sync_cart, name='sync_cart'),
    path('place-order/', views.place_order, name='place_order'),
    path('manage-orders/', views.manage_orders, name='manage_orders'),
    path('chef-panel/', views.chef_panel, name='chef_panel'),
    path('waiter-panel/', views.waiter_panel, name='waiter_panel'),
]