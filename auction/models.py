from django.db import models
from django.contrib.auth.models import User 

# Create your models here.

class AuctionUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=10)
    address = models.CharField(max_length=200)

    def __str__(self):
        return self.user.username
    
class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(null=True)    
    base_price = models.IntegerField(default=0)
    status = models.CharField(max_length=20, default='Active')
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return self.name

class Auction(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='auction_selling')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    higest_bid = models.DecimalField(decimal_places=2, default=0.0, max_digits=15)
    winner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='auction_won')

    def __str__(self):
        return self.product.name
    
class Bid(models.Model):
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE)
    bidder = models.ForeignKey(User, on_delete=models.CASCADE)
    bid_amount = models.DecimalField(decimal_places=2, max_digits=15)
    bid_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.auction.product.name


