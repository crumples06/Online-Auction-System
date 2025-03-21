from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('login/', views.loginPage, name='login'),
    path('logout/', views.logoutUser, name='logout'),
    path('register/', views.registerPage, name='register'),

    path('', views.home, name='home'),
    path('auctions/', views.auctions, name='auctions'),
    path('item/<str:pk>/', views.item, name='item'),
    path('profile/<str:pk>/', views.userProfile, name='userProfile'),
    path('add_auction/', views.add_auction, name='add_auction'),
    path('add_product/', views.add_product, name='add_product'),
    path('watchlist/add/<str:pk>', views.add_to_watchlist, name='add_to_watchlist'),
    path('watchlist/remove/<str:pk>', views.remove_from_watchlist, name='remove_from_watchlist'),
    path('watchlist/', views.watchlist, name='watchlist'),

]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)