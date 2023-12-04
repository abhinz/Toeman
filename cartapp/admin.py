from django.contrib import admin

# Register your models here.
from.models import *




class CartAdmin(admin.ModelAdmin):
    list_display=('cart_id','user','date_added')

admin.site.register(Cart,CartAdmin)


class CartItemAdmin(admin.ModelAdmin):
    list_display=('id','user','product','variant','size','cart','quantity')

admin.site.register(CartItem,CartItemAdmin)