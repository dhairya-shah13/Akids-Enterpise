from django.urls import path
from . import api_views

urlpatterns = [
    path('search/', api_views.search_products, name='product_search'),
]
