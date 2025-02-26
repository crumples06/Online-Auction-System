from django.shortcuts import render
from .models import Product

# Create your views here.


def home(request):
    return render(request, 'home.html')

def auctions(request):
    auction_listings = Product.objects.all()
    context = {'auction_listings':auction_listings}
    return render(request, 'auctions.html', context)

def item(request, pk):
    item = Product.objects.get(id=pk)
    context = {'item':item}
    return render(request, 'item.html', context)
