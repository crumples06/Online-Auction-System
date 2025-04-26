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
    path('user/<int:user_id>/won-auctions/', views.won_auctions, name='won_auctions'),
    path('auction/<int:auction_id>/pay/', views.make_payment, name='make_payment'),
    path('auction/<int:auction_id>/confirm/', views.confirm_delivery, name='confirm_delivery'),
    path('price-prediction/', views.price_prediction, name='price_prediction'),
    
    # Wallet URLs
    path('wallet/', views.wallet_dashboard, name='wallet_dashboard'),
    path('wallet/add-funds/', views.add_funds, name='add_funds'),
    path('wallet/payment/<int:transaction_id>/', views.process_payment, name='process_payment'),
    
    # Chat URLs
    path('auction/<int:auction_id>/chat/', views.auction_chat, name='auction_chat'),
    path('auction/<int:auction_id>/chat/send/', views.send_message, name='send_message'),
    path('auction/<int:auction_id>/chat/get/', views.get_messages, name='get_messages'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)