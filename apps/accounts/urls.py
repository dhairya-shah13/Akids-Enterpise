from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('address/<int:address_id>/edit/', views.edit_address_view, name='edit_address'),
    path('address/<int:address_id>/delete/', views.delete_address_view, name='delete_address'),
    path('address/<int:address_id>/set-default/', views.set_default_address_view, name='set_default_address'),
    path('orders/', views.order_history_view, name='order_history'),
]
