from django.urls import path
from django.views.generic import TemplateView
from . import views

urlpatterns = [
    path('', TemplateView.as_view(template_name='products/home.html'), name='home'),
    path('indoors/', views.indoors_view, name='indoors'),
    path('outdoors/', views.outdoors_view, name='outdoors'),
    path('parts/', views.parts_view, name='parts'),
    path('rfsports/', views.rfsports_view, name='rfsports'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    
    # Admin & Auth Routes
    path('login/', views.login_view, name='admin_login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='admin_logout'),
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:pk>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:pk>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:pk>/', views.update_cart, name='update_cart'),
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/products/add/', views.add_product, name='add_product'),
    path('admin-panel/products/<int:pk>/delete/', views.delete_product, name='delete_product'),
]
