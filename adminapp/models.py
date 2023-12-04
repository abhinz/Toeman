from django.db import models
from mainapp.models import *
# Create your models here.



class Offers(models.Model):
    DISCOUNT_CHOICES = [
        ('percentage', 'Percentage'),
        ('amount', 'Amount'),
    ]
    name=models.CharField(max_length=100)
    discount_on=models.CharField(max_length=100)
    product= models.ForeignKey(Products, on_delete=models.CASCADE,null=True,blank=True)
    category= models.ForeignKey(Category, on_delete=models.CASCADE,null=True,blank=True)
    discount_type=models.CharField(max_length=100, choices=DISCOUNT_CHOICES)
    discount_value=models.CharField(max_length=100)
    valid_from=models.DateTimeField()
    valid_to=models.DateTimeField()
    is_unlisted=models.BooleanField(default=False)


    def __str__(self):
        return self.name
