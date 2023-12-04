from django.urls import path
from . import views

urlpatterns = [

    path('',views.home,name='home'),
    path('product_list',views.product_list,name='product_list'),
    path('invoice',views.invoice,name='invoice'),
    path('product/<int:p_id>/', views.product, name='product_detail'),


    path('profile/<int:uid>/', views.profile, name='profile'),
    path('profile_view/<int:uid>/', views.profile_view, name='profile_view'),
    path('profile_edit/<int:uid>/', views.profile_edit, name='profile_edit'),
    path('profile_address/<int:uid>/', views.profile_address, name='profile_address'),
    path('profile_edit_address/<int:uid>/edit_address/<int:address_id>/', views.profile_edit_address, name='profile_edit_address'),
    path('delete_user/', views.delete_user, name='delete_user'),
    path('delete_address/<int:uid>/<int:address_id>/', views.delete_address, name='delete_address'),
    path('make_default_address/<int:uid>/<int:address_id>/', views.make_default_address, name='make_default_address'),

    path('profile_orders/', views.profile_orders, name='profile_orders'),
    path('my_coupons/', views.my_coupons, name='my_coupons'),

    path('profile_order_view/<int:order_id>/',views.profile_order_view, name='profile_order_view'),
    path('cancel_order/<int:order_id>/', views.cancel_order, name='cancel_order'),
    path('return_order/<int:order_id>/', views.return_order, name='return_order'),

    path('add_to_wishlist/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('view_wishlist/', views.view_wishlist, name='view_wishlist'),
    path('remove_from_wishlist/<int:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),

    path('my_wallet', views.my_wallet, name='my_wallet'),

    path('contact/', views.contact, name='contact'),
    path('about/', views.about, name='about'),
    path('eg/', views.eg, name='eg'),


    path('add_review/<int:p_id>/', views.add_review, name='add_review'),
    path('edit_review/<int:review_id>/', views.edit_review, name='edit_review'),
    path('delete_review/<int:review_id>/', views.delete_review, name='delete_review'),

]
