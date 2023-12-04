from django.urls import path
from . import views

urlpatterns = [
    path('admin_login/', views.admin_login, name='admin_login'),
    path('admin_home/', views.admin_home, name='admin_home'),
    path('add_product/', views.add_product, name='add_product'),
    path('admin_logout/', views.admin_logout, name='admin_logout'),

    path('admin_products_list/', views.admin_products_list, name='admin_products_list'),
    path('edit_products/<int:p_id>/',views.edit_products,name='edit_products'),
    path('soft_delete_product/<int:d_id>/',views.soft_delete_product,name='soft_delete_product'),
    path('undo_soft_delete_product/<int:d_id>/',views.undo_soft_delete_product,name='undo_soft_delete_product'),

    path('add_categories',views.add_categories,name='add_categories'),
    path('edit_categories/<int:c_id>/',views.edit_categories,name='edit_categories'),
    path('soft_delete_category/<int:c_id>/', views.soft_delete_category, name='soft_delete_category'),
    path('undo_soft_delete_category/<int:c_id>/', views.undo_soft_delete_category, name='undo_soft_delete_category'),


    path('user_list/',views.user_list,name='user_list'),
    path('block_user/<int:u_id>/',views.block_user,name='block_user'),
    path('unblock_user/<int:u_id>/', views.unblock_user, name='unblock_user'),


    path('order_list/',views.order_list,name='order_list'),
    path('order_detail/<int:order_id>',views.order_detail,name='order_detail'),


    path('sales', views.sales, name='sales'),
    path('today_sales',views.today_sales,name='today_sales'),
    path('current_year_sales',views.current_year_sales,name='current_year_sales'),
    path('update_order_status/<int:order_id>/<str:new_status>/', views.update_order_status, name='update_order_status'),


    path('coupon_list/', views.coupon_list, name='coupon_list'),
    path('add_coupons/', views.add_coupons, name='add_coupons'),
    path('edit_coupons/<int:coupon_id>/', views.edit_coupons, name='edit_coupons'),
    path('unlist_coupon/<int:c_id>/', views.unlist_coupon, name='unlist_coupon'),
    path('list_coupon/<int:c_id>/', views.list_coupon, name='list_coupon'),
    path('coupon_details/<int:coupon_id>/', views.coupon_details, name='coupon_details'),


    # path('delete_coupons/<int:coupon_id>/', views.delete_coupons, name='delete_coupons'),

    path('offer_list/',views.offer_list, name='offer_list'),
    path('add_offers/',views.add_offers, name='add_offers'),
    path('edit_offers/<int:o_id>/',views.edit_offers, name='edit_offers'),
    path('unlist/<int:o_id>/', views.unlist, name='unlist'),
    path('List/<int:o_id>/', views.List, name='List'),

    path('add_variants/<int:p_id>/', views.add_variants, name='add_variants'),
    path('unlist_variants/<int:p_id>/<int:v_id>/', views.unlist_variants, name='unlist_variants'),
    path('list_variants/<int:p_id>/<int:v_id>/', views.list_variants, name='list_variants'),
    path('edit_variants/<int:p_id>/<int:v_id>/', views.edit_variants, name='edit_variants'),

]