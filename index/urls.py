# urls.py (بروزرسانی شده برای APIهای جدید)
from django.urls import path
from . import views

app_name = 'index'

urlpatterns = [
    path('', views.home, name='home'),
    path('order/', views.order_menu, name='order_menu'),
    path('sync-cart/', views.sync_cart, name='sync_cart'),
    path('place-order/', views.place_order, name='place_order'),
    
    # پنل مدیر
    path('manage-orders/', views.manage_orders, name='manage_orders'),
    path('api/manager/orders/', views.get_manager_orders, name='get_manager_orders'),
    path('api/manager/confirm/<int:order_id>/', views.confirm_order, name='confirm_order'),
    path('api/manager/reject/<int:order_id>/', views.reject_order, name='reject_order'),
    
    # پنل آشپز
    path('chef-panel/', views.chef_panel, name='chef_panel'),
    path('api/chef/orders/', views.get_chef_orders, name='get_chef_orders'),
    path('api/chef/start/<int:order_id>/', views.start_cooking, name='start_cooking'),
    path('api/chef/finish/<int:order_id>/', views.finish_cooking, name='finish_cooking'),
    
    # پنل گارسون
    path('waiter-panel/', views.waiter_panel, name='waiter_panel'),
    path('api/waiter/orders/', views.get_waiter_orders, name='get_waiter_orders'),
    path('api/waiter/deliver/<int:order_id>/', views.deliver_order, name='deliver_order'),
]