from django.shortcuts import render, redirect
from django.contrib import messages
from .models import *
from .forms import *
from django.contrib.auth.models import User 
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import get_object_or_404
from django.utils.timezone import now

# Create your views here.

def loginPage(request):
    page = 'login'
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            user = User.objects.get(username=username)
        except:
            messages.error(request, 'User does not exist')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Username OR Password does not exist')

    context = {'page':page}
    return render(request, 'login_register.html', context)

def logoutUser(request):
    logout(request)
    return redirect('home')

def registerPage(request):
    form = UserCreationForm()

    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.save()
            login(request, user)
            return redirect('home')
        else:
           messages.error(request, 'An error occured during registration') 

    return render(request, 'login_register.html', {'form':form})

def home(request):
    return render(request, 'home.html')

def auctions(request):
    current_time = now()
    Auction.objects.filter(start_time__gt=current_time).update(status='Starting Soon')
    Auction.objects.filter(start_time__lte=current_time, end_time__gt=current_time).update(status='Active')
    Auction.objects.filter(end_time__lte=current_time).update(status='Closed')

    auction_listings = Auction.objects.exclude(status='Closed')
    context = {'auction_listings':auction_listings}
    return render(request, 'auctions.html', context)

def item(request, pk):
    auction = Auction.objects.get(id=pk)
    bids = auction.bid_set.all().order_by('-bid_time')
    current_time = now()

    if request.method == 'POST':
        bid_amount = float(request.POST.get('bid_amount'))
        if bid_amount >  float(auction.higest_bid) and bid_amount > float(auction.product.base_price):
            auction.higest_bid = bid_amount
            auction.winner = request.user
            auction.save()

            Bid.objects.create(auction=auction, bidder=request.user, bid_amount=bid_amount)
            messages.success(request, 'Your bid has been placed successfully.')
        else:
            messages.error(request, 'Your bid must be higher than the current highest bid.')

    context = {'auction':auction, 'bids':bids, 'now':current_time}
    return render(request, 'item.html', context)

@login_required(login_url='login')
def add_auction(request):
    form = AuctionForm()

    if request.method == 'POST':
        form = AuctionForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('home')

    context = {'form':form}
    return render(request, 'add_auction.html', context)

@login_required(login_url='login')
def add_product(request):
    form = ProductForm()
    files = request.FILES.getlist('images')

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()

            for file in files:
                ProductImage.objects.create(product=product, image=file)
            return redirect('add_auction')
        
    context = {'form':form}
    return render(request, 'add_product.html', context)

def userProfile(request, pk):
    user = User.objects.get(id=pk)
    auction = user.auction_selling.all().order_by('-start_time')
    context = {'user':user, 'auction':auction}
    return render(request, 'profile.html', context)
