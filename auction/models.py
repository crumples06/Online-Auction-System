from django.db import models
from django.contrib.auth.models import User 

# Create your models here.

class AuctionUser(models.Model):
    name = models.CharField(max_length=200)
    email = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=10)
    address = models.TextField()
    registered_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(null=True)    
    base_price = models.IntegerField(default=0)
    status = models.CharField(max_length=20)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Participant(models.Model):
    user = models.ForeignKey(AuctionUser, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    joined = models.DateTimeField(auto_now_add=True)

