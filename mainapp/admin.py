from django.contrib import admin
from .models import *
# Register your models here.


admin.site.register(Category)
admin.site.register(Products)
admin.site.register(Profile)
admin.site.register(Address)
admin.site.register(Wallet)
admin.site.register(Reffer)
# admin.site.register(Reviews)

class UserReviews(admin.ModelAdmin):
    list_display=('id','user','product','comment')

admin.site.register(Reviews,UserReviews)






class ProductAttributeAdmin(admin.ModelAdmin):
    list_display=('id','product','size','quantity')

admin.site.register(ProductAttribute,ProductAttributeAdmin)