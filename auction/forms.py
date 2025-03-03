from django.forms import ModelForm, DateTimeInput
from .models import Auction, Product, AuctionUser, ProductImage
from django import forms


class AuctionForm(ModelForm):
    class Meta:
        model = Auction
        fields = '__all__'
        widgets = {
            'start_time': DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class ProductForm(ModelForm):
    class Meta:
        model = Product
        fields = '__all__'
