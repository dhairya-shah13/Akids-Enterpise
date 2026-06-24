from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('rf-sports/', views.RFSportsView.as_view(), name='rf_sports'),
]
