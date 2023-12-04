from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import User


class Products(models.Model):
    product_name = models.CharField(max_length=200, blank=True, null=True)
    brand_name = models.CharField(max_length=200 ,blank=True, null=True)
    old_price = models.CharField(max_length=200,blank=True, null=True)
    price = models.IntegerField(blank=True, null=True)
    colors = models.CharField(max_length=100, blank=True, null=True)
    # sizes = models.CharField(max_length=100, blank=True, null=True)

    description = models.TextField(blank=True, null=True)
    product_image1 = models.ImageField(upload_to='media/product/img1', blank=True, null=True)
    product_image2 = models.ImageField(upload_to='media/product/img2', blank=True, null=True)
    product_image3 = models.ImageField(upload_to='media/product/img3', blank=True, null=True)
    product_image4 = models.ImageField(upload_to='media/product/img4', blank=True, null=True)
    product_image5 = models.ImageField(upload_to='media/product/img5', blank=True, null=True)

    # quantity = models.IntegerField(blank=True, null=True)
    is_avialable = models.BooleanField('Is available', default=False, blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    category = models.ForeignKey('Category', on_delete=models.CASCADE, default=False, blank=True, null=True)
    soft_delete = models.BooleanField(default=False)

    material = models.CharField(max_length=200,blank=True, null=True)
    special_feature = models.CharField(max_length=200,blank=True, null=True)
    fit_type = models.CharField(max_length=200,blank=True, null=True)
    shoe_width = models.IntegerField(blank=True, null=True)
    rating=models.FloatField(default=0,null=True)



    def __str__(self):
        return self.product_name

    def soft_delete_product(self):
        self.soft_delete = True
        self.save()

    def undo_soft_delete_product(self):
        self.soft_delete = False
        self.save()




class Category(models.Model):
    category_name = models.CharField(max_length=200)
    category_image = models.ImageField(upload_to='media/category')
    category_desc = models.TextField()
    soft_delete = models.BooleanField(default=False)

    def soft_delete_category(self):
        self.soft_delete = True
        self.save()

    def undo_soft_delete_category(self):
        self.soft_delete = False
        self.save()

    def __str__(self):
        return self.category_name



class Profile(models.Model):
    profile_image=models.ImageField(upload_to='profile',default='profile/profile.png')
    user=models.ForeignKey(User,on_delete=models.CASCADE)





class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone = models.CharField(max_length=15)
    email = models.EmailField(max_length=50)
    locality = models.CharField(max_length=150)
    landmark = models.CharField(max_length=150)
    house_name = models.CharField(max_length=150)
    city =models.CharField(max_length=50)
    state =models.CharField(max_length=50)
    pincode = models.CharField(max_length=10)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return self.first_name


class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Products, on_delete=models.CASCADE)



class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    amount = models.FloatField(default=100)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Wallet for {self.user.username}"


class Reffer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    code=models.CharField(max_length=50)
    def __str__(self):
        return f"Reffer code for {self.user.username}"





class Reviews(models.Model):
    user=models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Products, on_delete=models.CASCADE)
    comment=models.TextField()
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    rating=models.IntegerField()
    def __str__(self):
        return f"comment of  {self.user.username} on {self.product.product_name}"






class ProductAttribute(models.Model):
    SIZE_CHOICES = [
        (6, 6),
        (7, 7),
        (8, 8),
        (9, 9),
        (10, 10),
    ]
    product=models.ForeignKey(Products,on_delete=models.CASCADE)
    size=models.PositiveIntegerField(choices=SIZE_CHOICES)
    quantity=models.PositiveIntegerField()
    unlist=models.BooleanField(default=False)

    def __str__(self):
        return  f"varaint for {self.product.product_name}"
