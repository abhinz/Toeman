from django.urls import path
from . import views


urlpatterns = [
    path('checkout/',views.checkout,name='checkout'),
    path('add_address/<int:uid>',views.add_address,name='add_address'),
    path('place_order/', views.place_order, name='place_order'),
    path('payments/<int:order_id>', views.payments, name='payments'),
    path('complete_order/<int:order_id>', views.complete_order, name='complete_order'),
    path('cash_on_delivery/<int:order_id>/', views.cash_on_delivery, name='cash_on_delivery'),
    path('order_confirmed/<int:order_id>/', views.order_confirmed, name='order_confirmed'),
    path('confirm_razorpay_payment/<int:order_id>/', views.confirm_razorpay_payment, name='confirm_razorpay_payment'),
    path('wallet_pay/<int:order_id>/', views.wallet_pay, name='wallet_pay'),
    path('apply_coupon/', views.apply_coupon, name='apply_coupon'),
    #path('refer_coupon/', views.refer_coupon, name='refer_coupon'),

]

