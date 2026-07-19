from django.urls import path
from django.views.generic import TemplateView
from . import views

urlpatterns = [
    path('', TemplateView.as_view(template_name='products/home.html'), name='home'),
    path('search/', views.search_view, name='search'),
    path('', views.home_view, name='home'),
    path('indoors/', views.indoors_view, name='indoors'),
    path('outdoors/', views.outdoors_view, name='outdoors'),
    path('rfsports/', views.rfsports_view, name='rfsports'),
    path('about/', views.company_page, {'page': 'about'}, name='about'),
    path('safety-standards/', views.company_page, {'page': 'safety'}, name='safety_standards'),
    path('testimonials/', views.company_page, {'page': 'testimonials'}, name='testimonials'),
    path('contact/', views.company_page, {'page': 'contact'}, name='contact'),
    path('privacy-policy/', views.company_page, {'page': 'privacy'}, name='privacy_policy'),
    path('terms-of-service/', views.company_page, {'page': 'terms'}, name='terms_of_service'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('inquiry/submit/', views.submit_inquiry, name='submit_inquiry'),
    
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
    path('admin-panel/inquiries/<int:pk>/status/', views.update_inquiry_status, name='update_inquiry_status'),
    path('admin-panel/inquiries/<int:pk>/delete/', views.delete_inquiry, name='delete_inquiry'),
    path('api/chat/', views.chat_api, name='chat_api'),
]
