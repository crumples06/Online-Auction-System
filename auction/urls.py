from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('auctions/', views.auctions, name='auctions'),
    path('item/<str:pk>/', views.item, name='item')
]