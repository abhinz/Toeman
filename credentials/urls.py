from django.urls import path
from . import views
from .views import CustomLogoutView
from django.contrib.auth.views import PasswordResetView
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('register/',views.register,name='register'),
    path('login/',views.Login,name='login'),
    # path('logout/',views.Logout,name='logout'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('otp_verification',views.otp_verification,name="otp_verification"),
    path('resend_otp/', views.resend_otp, name='resend_otp'),
    path('otp_page/', views.otp_page, name='otp_page'),


    path('forgot_password/', views.forgot_password, name='forgot_password'),
    path('confirm_password/', views.confirm_password, name='confirm_password'),
    path('confirm_password_profile/', views.confirm_password_profile, name='confirm_password_profile'),


    path('profile_change_password/<int:uid>/', views.profile_change_password, name='profile_change_password'),


]





