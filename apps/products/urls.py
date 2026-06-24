from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('indoor/', views.product_list_view, {'category_type': 'indoor'}, name='indoor'),
    path('outdoor/', views.product_list_view, {'category_type': 'outdoor'}, name='outdoor'),
    path('parts/', views.product_list_view, {'category_type': 'parts'}, name='parts'),
    path('<slug:slug>/', views.product_detail_view, name='detail'),
]
