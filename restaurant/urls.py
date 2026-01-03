from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='restaurant/registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('menu/', views.menu_view, name='menu'),
    path('add-to-cart/<int:item_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart_view, name='cart'),
    path('update-cart/<int:item_id>/', views.update_cart_item, name='update_cart'),
    path('remove-from-cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('orders/', views.orders_view, name='orders'),
    path('receipt/<int:order_id>/', views.receipt_view, name='receipt'),
    path('analytics/', views.analytics_view, name='analytics'),
    
    # Category Management
    path('manage/categories/', views.category_list, name='category_list'),
    path('manage/categories/add/', views.category_add, name='category_add'),
    path('manage/categories/edit/<int:category_id>/', views.category_edit, name='category_edit'),
    path('manage/categories/delete/<int:category_id>/', views.category_delete, name='category_delete'),
    
    # Menu Item Management
    path('manage/menu-items/', views.menuitem_list, name='menuitem_list'),
    path('manage/menu-items/add/', views.menuitem_add, name='menuitem_add'),
    path('manage/menu-items/edit/<int:item_id>/', views.menuitem_edit, name='menuitem_edit'),
    path('manage/menu-items/delete/<int:item_id>/', views.menuitem_delete, name='menuitem_delete'),
    path('manage/menu-items/toggle/<int:item_id>/', views.menuitem_toggle_availability, name='menuitem_toggle'),
]