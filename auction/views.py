from django.shortcuts import render, redirect
from django.contrib import messages
from .models import *
from .forms import *
from .utils import *
from django.contrib.auth.models import User 
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import get_object_or_404
from django.utils.timezone import now, timedelta
from decimal import Decimal
from django.http import Http404, JsonResponse
from django.db import models
from django.db.models import F

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
    form = CustomUserCreationForm()

    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.first_name = form.cleaned_data['first_name']  
            user.last_name = form.cleaned_data['last_name']
            user.email = form.cleaned_data['email']
            user.save()

            AuctionUser.objects.create(
                user=user,
                phone_number=form.cleaned_data['phone_number'],
                address=form.cleaned_data['address']
            )
            
            # Create a wallet for the new user
            Wallet.objects.create(user=user, balance=0)
            
            login(request, user)
            return redirect('home')
        else:
           messages.error(request, 'An error occured during registration') 

    return render(request, 'login_register.html', {'form':form})

def home(request):
    # Get current time to determine auction status
    current_time = now()
    
    # Update auction statuses
    Auction.objects.filter(start_time__gt=current_time).update(status='Starting Soon')
    Auction.objects.filter(start_time__lte=current_time, end_time__gt=current_time).update(status='Active')
    Auction.objects.filter(end_time__lte=current_time).update(status='Closed')
    
    # Get featured auctions - active auctions with highest bids (limit to 4)
    featured_auctions = Auction.objects.filter(
        status='Active'
    ).order_by('-higest_bid')[:4]  # Get top 4 auctions with highest bids
    
    # Initialize watched_auctions_ids for authenticated users
    watched_auctions_ids = []
    if request.user.is_authenticated:
        watched_auctions_ids = request.user.watchlist.all().values_list('auction_id', flat=True)
    
    context = {
        'featured_auctions': featured_auctions,
        'watched_auctions_ids': watched_auctions_ids,
    }
    return render(request, 'home.html', context)

def auctions(request):
    current_time = now()
    Auction.objects.filter(start_time__gt=current_time).update(status='Starting Soon')
    Auction.objects.filter(start_time__lte=current_time, end_time__gt=current_time).update(status='Active')
    Auction.objects.filter(end_time__lte=current_time).update(status='Closed')

    # Start with all active auctions
    auction_listings = Auction.objects.exclude(status='Closed')
    
    # Handle form submissions
    if request.method == 'GET':
        # Search by keyword
        search_query = request.GET.get('search', '')
        if search_query:
            auction_listings = auction_listings.filter(
                models.Q(product__name__icontains=search_query) | 
                models.Q(product__description__icontains=search_query)
            )
        
        # Filter by category
        categories = request.GET.getlist('category')
        if categories:
            auction_listings = auction_listings.filter(product__category__in=categories)
        
        # Filter by price range
        min_price = request.GET.get('min_price')
        if min_price and min_price.isdigit():
            auction_listings = auction_listings.filter(higest_bid__gte=min_price)
            
        max_price = request.GET.get('max_price')
        if max_price and max_price.isdigit():
            auction_listings = auction_listings.filter(higest_bid__lte=max_price)
        
        # Filter by status
        status_filter = request.GET.get('status')
        if status_filter == 'live':
            auction_listings = auction_listings.filter(status='Active')
        elif status_filter == 'ending':
            # Ending soon means ending in the next 24 hours
            ending_soon_time = current_time + timedelta(hours=24)
            auction_listings = auction_listings.filter(
                status='Active', 
                end_time__lte=ending_soon_time
            )
        elif status_filter == 'upcoming':
            auction_listings = auction_listings.filter(status='Starting Soon')
        
        # Sort results
        sort_by = request.GET.get('sort')
        if sort_by == 'newest':
            auction_listings = auction_listings.order_by('-start_time')
        elif sort_by == 'ending':
            auction_listings = auction_listings.order_by('end_time')
        elif sort_by == 'price_low':
            auction_listings = auction_listings.order_by('higest_bid')
        elif sort_by == 'price_high':
            auction_listings = auction_listings.order_by('-higest_bid')
    
    context = {
        'auction_listings': auction_listings,
        'search_query': request.GET.get('search', ''),
        'selected_categories': request.GET.getlist('category'),
        'min_price': request.GET.get('min_price', ''),
        'max_price': request.GET.get('max_price', ''),
        'status_filter': request.GET.get('status', 'all'),
        'sort_by': request.GET.get('sort', 'newest')
    }
    return render(request, 'auctions.html', context)

def item(request, pk):
    auction = get_object_or_404(Auction, id=pk)
    bids = auction.bid_set.all().order_by('-bid_time')
    reviews = Review.objects.filter(auction=auction)
    current_time = now()
    form = None

    can_review = request.user.is_authenticated and request.user == auction.winner and auction.end_time <= current_time
    has_reviewed = Review.objects.filter(auction=auction, winner=request.user).exists() if request.user.is_authenticated else False

    # Get chat access information for the template
    can_access_chat = request.user.is_authenticated
    
    if request.method == 'POST':
        if 'bid_submit' in request.POST:  # Handle Bidding
            if not request.user.is_authenticated:
                messages.error(request, "You need to log in to place a bid.")
                return redirect('login')
                
            # Get or create wallet
            wallet, created = Wallet.objects.get_or_create(user=request.user)
            bid_amount = Decimal(request.POST.get('bid_amount'))
            
            # Check if user has enough balance
            if bid_amount > wallet.balance:
                messages.error(request, f"Insufficient funds. Your wallet balance is ₹{wallet.balance}. Add more funds to place this bid.")
                return redirect('item', pk=auction.id)

            if bid_amount > Decimal(auction.higest_bid) and bid_amount > Decimal(auction.product.base_price):
                previous_winner = auction.winner

                auction.higest_bid = bid_amount

                #Auto extending time to prevent bid sniping
                remaining_time = (auction.end_time - now()).total_seconds()
                if remaining_time < 300:  # If less than 5 minutes remaining
                    auction.end_time = auction.end_time + timedelta(minutes=5)
                    
                auction.winner = request.user
                auction.save()

                # Record the bid
                Bid.objects.create(
                    auction=auction,
                    bidder=request.user,
                    bid_amount=bid_amount
                )
                
                # Add system message about the bid in the chat
                AuctionMessage.objects.create(
                    auction=auction,
                    user=request.user,
                    message=f"{request.user.username} placed a bid of ₹{bid_amount}",
                    is_system_message=True
                )
                
                messages.success(request, f"Bid placed successfully! You are now the highest bidder at ₹{bid_amount}.")
            else:
                messages.error(request, "Your bid must be higher than the current highest bid.")
                
        elif 'review_submit' in request.POST and can_review and not has_reviewed:
            rating = request.POST.get('rating')
            comment = request.POST.get('comment')
            
            if rating and comment:
                Review.objects.create(
                    auction=auction,
                    winner=request.user,
                    seller=auction.seller,
                    rating=rating,
                    comment=comment
                )
                messages.success(request, "Your review has been submitted. Thank you for your feedback!")
                return redirect('item', pk=auction.id)
            else:
                messages.error(request, "Both rating and comment are required.")
    
    # Get user's wallet balance if authenticated
    wallet_balance = 0
    if request.user.is_authenticated:
        wallet, created = Wallet.objects.get_or_create(user=request.user)
        wallet_balance = wallet.balance
    
    # Get ratings for seller if there are any reviews
    seller_reviews = Review.objects.filter(seller=auction.seller)
    avg_rating = seller_reviews.aggregate(avg=models.Avg('rating'))['avg'] if seller_reviews else 0
    total_reviews = seller_reviews.count()
    
    context = {
        'auction': auction,
        'bids': bids,
        'watched_auctions_ids': request.user.watchlist.all().values_list('auction_id', flat=True) if request.user.is_authenticated else [],
        'now': current_time,
        'wallet_balance': wallet_balance,
        'can_review': can_review,
        'has_reviewed': has_reviewed,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'total_reviews': total_reviews,
        'can_access_chat': can_access_chat
    }
    return render(request, 'item.html', context)

@login_required(login_url='login')
def add_auction(request):
    form = AuctionForm(user=request.user)
    if request.method == 'POST':
        form = AuctionForm(request.POST, user=request.user)
        if form.is_valid():
            auction = form.save(commit=False)
            auction.seller = request.user  # Set seller automatically
            auction.status = "Starting Soon" if auction.start_time > now() else "Active"
            auction.save()
            messages.success(request, "Auction created successfully!")
            return redirect('item', pk=auction.pk)

    context = {'form':form}
    return render(request, 'add_auction.html', context)

@login_required(login_url='login')
def add_product(request):
    form = ProductForm()
    files = request.FILES.getlist('images')

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.owner = request.user
            product.save()
            
            for file in files:
                ProductImage.objects.create(product=product, image=file)
            return redirect('add_auction')
        
    context = {'form':form}
    return render(request, 'add_product.html', context)

def userProfile(request, pk):
    user = User.objects.get(id=pk)
    seller = get_object_or_404(AuctionUser, user=user)
    reviews = Review.objects.filter(seller=user).order_by('-created_at')
    auction = user.auction_selling.all().order_by('-start_time')
    
    # Calculate average rating
    avg_rating = 0
    if reviews.exists():
        total_rating = sum(review.rating for review in reviews)
        avg_rating = round(total_rating / reviews.count(), 1)
    
    context = {
        'user': user, 
        'auction': auction, 
        'reviews': reviews, 
        'seller': seller,
        'avg_rating': avg_rating
    }
    return render(request, 'profile.html', context)


@login_required(login_url='login')
def watchlist(request):
    items = Watchlist.objects.filter(user=request.user).select_related('auction')
    context = {'watchlist_items' : items}
    return render(request, 'watchlist.html', context)

def add_to_watchlist(request, pk):
    auction = Auction.objects.get(id=pk)
    Watchlist.objects.get_or_create(user=request.user, auction=auction)
    return redirect('item', pk=pk)

def remove_from_watchlist(request, pk):
    auction = Auction.objects.get(id=pk)
    Watchlist.objects.filter(user=request.user, auction=auction).delete()
    return redirect('item', pk=pk)

@login_required(login_url='login')
def won_auctions(request, user_id):
    if request.user.id != user_id:
        raise Http404("You are not authorized to view this page.")
    
    won_auctions = Auction.objects.filter(winner=request.user, end_time__lte=now())
    context = {'won_auctions': won_auctions}
    return render(request, 'won_auctions.html', context)

@login_required
def confirm_delivery(request, auction_id):
    auction = get_object_or_404(Auction, id=auction_id)

    if auction.winner != request.user or not auction.is_paid:
        messages.error(request, "You can't confirm this delivery.")
        return redirect('item', pk=auction_id)

    if request.method == 'POST':
        auction.is_delivered = True
        auction.save()
        messages.success(request, "Delivery confirmed. Thank you!")  
        return redirect('item', pk=auction_id)

    return redirect('item', pk=auction_id)



@login_required
def make_payment(request, auction_id):
    auction = get_object_or_404(Auction, id=auction_id)

    if auction.winner != request.user:
        messages.error(request, "You are not authorized to make this payment.")
        return redirect('item', pk=auction_id)

    if auction.end_time > now():
        messages.error(request, "Auction has not ended yet.")
        return redirect('item', pk=auction_id)

    if request.method == 'POST':
        auction.is_paid = True
        auction.save()
        messages.success(request, "Payment successful!")
        return redirect('item', pk=auction_id)

    return redirect('item', pk=auction_id)

@login_required(login_url='login')
def price_prediction(request):
    return render(request, 'price_prediction.html')

# Wallet views
@login_required(login_url='login')
def wallet_dashboard(request):
    # Get or create wallet for the user
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    
    # Get transactions
    transactions = WalletTransaction.objects.filter(wallet=wallet).order_by('-timestamp')
    
    context = {
        'wallet': wallet,
        'transactions': transactions,
    }
    return render(request, 'wallet_dashboard.html', context)

@login_required(login_url='login')
def add_funds(request):
    # Get or create wallet for the user
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        amount = Decimal(request.POST.get('amount', 0))
        
        if amount < 100:
            messages.error(request, "Minimum amount to add is ₹100.")
            return redirect('add_funds')
            
        # Create a pending transaction
        transaction = WalletTransaction.objects.create(
            wallet=wallet,
            amount=amount,
            transaction_type='DEPOSIT',
            status='PENDING',
            description='Wallet funding'
        )
        
        # Redirect to payment processing
        return redirect('process_payment', transaction_id=transaction.id)
        
    context = {
        'wallet': wallet,
    }
    return render(request, 'add_funds.html', context)

@login_required(login_url='login')
def process_payment(request, transaction_id):
    # Get the transaction
    transaction = get_object_or_404(WalletTransaction, id=transaction_id)
    
    # Ensure the transaction belongs to the current user
    if transaction.wallet.user != request.user:
        messages.error(request, "You don't have permission to view this transaction.")
        return redirect('wallet_dashboard')
    
    # If the transaction is already processed, redirect to wallet dashboard
    if transaction.status != 'PENDING':
        return redirect('wallet_dashboard')
    
    if request.method == 'POST':
        # This is a demo implementation. In a real application, you would integrate with a payment gateway
        # For demo purposes, we'll just mark the transaction as successful and update the wallet balance
        
        transaction.status = 'SUCCESS'
        transaction.save()
        
        # Update wallet balance
        wallet = transaction.wallet
        wallet.balance = F('balance') + transaction.amount
        wallet.save()
        
        messages.success(request, f"Successfully added ₹{transaction.amount} to your wallet.")
        return redirect('wallet_dashboard')
    
    context = {
        'transaction': transaction,
    }
    return render(request, 'process_payment.html', context)

@login_required(login_url='login')
def auction_chat(request, auction_id):
    auction = get_object_or_404(Auction, id=auction_id)
    
    # No longer checking if user is participant or seller - any authenticated user can view
    
    # Get messages for this auction
    chat_messages = AuctionMessage.objects.filter(auction=auction).order_by('created_at')
    
    context = {
        'auction': auction,
        'chat_messages': chat_messages,
    }
    return render(request, 'auction_chat.html', context)

@login_required(login_url='login')
def send_message(request, auction_id):
    auction = get_object_or_404(Auction, id=auction_id)
    
    # Any authenticated user can send messages now
    
    if request.method == 'POST':
        message_text = request.POST.get('message', '').strip()
        
        if message_text:
            # Create the message
            message = AuctionMessage.objects.create(
                auction=auction,
                user=request.user,
                message=message_text
            )
            
            # Return a JSON response for AJAX requests
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'message_id': message.id,
                    'username': message.user.username,
                    'message': message.message,
                    'timestamp': message.created_at.strftime('%b %d, %Y, %I:%M %p'),
                    'is_sender': True
                })
            
            # For non-AJAX requests redirect back to the auction page
            return redirect('auction_chat', auction_id=auction_id)
    
    return redirect('auction_chat', auction_id=auction_id)

@login_required(login_url='login')
def get_messages(request, auction_id):
    auction = get_object_or_404(Auction, id=auction_id)
    
    # All authenticated users can view chat messages
    
    # Get the last message ID from the request to fetch only newer messages
    last_message_id = request.GET.get('last_id', 0)
    
    # Get messages newer than the last ID
    new_messages = AuctionMessage.objects.filter(
        auction=auction, 
        id__gt=last_message_id
    ).order_by('created_at')
    
    # Format messages for JSON response
    messages_data = []
    for message in new_messages:
        messages_data.append({
            'id': message.id,
            'username': message.user.username,
            'message': message.message,
            'timestamp': message.created_at.strftime('%b %d, %Y, %I:%M %p'),
            'is_sender': message.user.id == request.user.id,
            'is_system': message.is_system_message
        })
    
    return JsonResponse({'status': 'success', 'messages': messages_data})

