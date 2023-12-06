from datetime import timezone

from django.db import models
from mainapp.models import *

# Create your models here.



class Order(models.Model):
    STATUS = [
        ('New', 'New'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
        ('Returned', 'Returned'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    order_number = models.CharField(max_length=200)
    address=models.ForeignKey(Address,on_delete=models.SET_NULL,blank=True,null=True)
    order_total = models.FloatField()
    shipping = models.FloatField()
    tax = models.FloatField()
    status = models.CharField(max_length=100, choices=STATUS, default='New')
    is_ordered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    discount = models.FloatField(default=0)


    def __str__(self):
        if self.user:
            return f"Order {self.order_number} for {self.user.username}"
        else:
            return f"Order {self.order_number} (No user assigned)"


class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    payment_method = models.CharField(max_length=100,default='Cancelled')
    amount_paid = models.FloatField(default=0)
    status = models.CharField(max_length=100)
    discount = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.payment_method

class OrderProduct(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Products, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductAttribute, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    product_price = models.FloatField()
    ordered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    size = models.IntegerField()


    def __str__(self):
        return self.product.product_name





class Coupons(models.Model):
    coupon_code = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    minimum_amount = models.IntegerField(default=10000)
    discount = models.IntegerField(default=0)
    is_expired = models.BooleanField(default=False)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    un_list= models.BooleanField(default=False)

    def __str__(self):
        return self.coupon_code

    def is_valid(self):
        now = timezone.now()
        return now >= self.valid_from and now <= self.valid_to


    def is_used_by_user(self, user):
        redeemed_details = UserCoupons.objects.filter(coupon=self, user=user, is_used=True)
        return redeemed_details.exists()


class UserCoupons(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    coupon = models.ForeignKey(Coupons, on_delete=models.CASCADE)
    is_used = models.BooleanField(default=True)

    def __str__(self):
        return self.coupon.coupon_code