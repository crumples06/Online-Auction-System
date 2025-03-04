from django.contrib import admin

# Register your models here.

from .models import *

admin.site.register(AuctionUser)
admin.site.register(Product)
admin.site.register(Auction)
admin.site.register(Bid)
admin.site.register(ProductImage)
admin.site.register(Review)
