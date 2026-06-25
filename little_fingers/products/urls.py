from django.urls import path
from django.views.generic import TemplateView

urlpatterns = [
    path('', TemplateView.as_view(template_name='products/home.html'), name='home'),
    path('indoors/', TemplateView.as_view(template_name='products/listing.html'), name='indoors'),
    path('outdoors/', TemplateView.as_view(template_name='products/outdoors.html'), name='outdoors'),
    path('parts/', TemplateView.as_view(template_name='products/parts.html'), name='parts'),
    path('rfsports/', TemplateView.as_view(template_name='products/rfsports.html'), name='rfsports'),
]
