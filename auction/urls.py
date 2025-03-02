from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.loginPage, name='login'),
    path('logout/', views.logoutUser, name='logout'),
    path('register/', views.registerPage, name='register'),

    path('', views.home, name='home'),
    path('auctions/', views.auctions, name='auctions'),
    path('item/<str:pk>/', views.item, name='item'),
    path('add_auction/', views.add_auction, name='add_auction'),
    path('add_product/', views.add_product, name='add_product'),

]