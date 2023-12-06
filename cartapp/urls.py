from django.urls import path
from . import views

urlpatterns = [
    path('cart', views.cart, name='cart'),
    path('add_cart/<int:product_id>/', views.add_cart, name='add_cart'),
    path('add_to_cart_short/<int:product_id>/', views.add_to_cart_short, name='add_to_cart_short'),
    path('remove_cart/<int:product_id>/', views.remove_cart, name='remove_cart'),
    path('remove_cart_item/<int:product_id>/', views.remove_cart_item, name='remove_cart_item'),
    path('cart_plus/<int:variant_id>/', views.cart_plus, name='cart_plus'),
]
