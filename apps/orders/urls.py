from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('checkout/', views.checkout_view, name='checkout'),
    path('payment/<str:order_number>/simulate/', views.payment_simulate_view, name='payment_simulate'),
    path('payment/<str:order_number>/process/', views.payment_process_view, name='payment_process'),
    path('<str:order_number>/confirm/', views.order_confirm_view, name='order_confirm'),
]
