from django.forms import ModelForm, DateTimeInput
from .models import Auction, Product, AuctionUser, ProductImage, Review
from django import forms
from django.utils.timezone import now
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm


class AuctionForm(ModelForm):
    class Meta:
        model = Auction
        fields = ['product', 'start_time', 'end_time']
        widgets = {
            'start_time': DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def clean_start_time(self):
        start_time = self.cleaned_data.get('start_time')
        if start_time and start_time < now():
            raise forms.ValidationError("Start time cannot be in the past.")
        return start_time
    
    def clean_end_time(self):
        start_time = self.cleaned_data.get('start_time')
        end_time = self.cleaned_data['end_time']
        if start_time and end_time <= start_time:
            raise forms.ValidationError("End time must be after the start time.")
        return end_time

class ProductForm(ModelForm):
    class Meta:
        model = Product
        fields = '__all__'


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(max_length=10)
    address = forms.CharField(max_length=200, widget=forms.Textarea(attrs={'rows': 2}))

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'phone_number', 'address']

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
