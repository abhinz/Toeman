from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.core.validators import validate_email
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
import random
from django.core.mail import send_mail
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.core.exceptions import ValidationError
import datetime
import time
import string
from django.views import View

from mainapp.models import Reffer, Wallet


@never_cache
def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        c_password = request.POST.get('cpassword')
        code = request.POST.get('code')
        print(code)

        request.session['username'] = username
        request.session['email'] = email
        request.session['password'] = password
        request.session['code'] = code

        try:
            if not username or not email or not password:
                messages.error(request, 'Enter details to field')
                return redirect('register')
        except:
            pass

        try:
            if User.objects.filter(username=username).exists():
                messages.error(request, "Username already exists. Please choose a different one.")
                return redirect("register")
            elif not username.isalnum():
                messages.warning(request, "Username contains invalid characters. Please use only letters and numbers.")
                return redirect("register")
        except:
            pass

        try:
            if User.objects.filter(email=email):
                messages.error(request, "Email already exists")
                return redirect("register")
        except:
            pass

        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, "Invalid email address")
            return redirect('/signup')

        try:
            if password != c_password:
                messages.error(request, "passwords not matching")
                return redirect("register")
        except:
            pass

        try:
            if len(username) > 20:
                messages.error(request, "username is too long")
                return redirect("register")
        except:
            pass

        try:
            if len(password) < 8:
                messages.error(request, "Password must be at least 8 characters")
                return redirect("register")
        except:
            pass

        request.session['verification_type'] = 'register'
        send_otp(request)
        return render(request, 'otp.html', {"email": email})

    return render(request, 'credentials/register.html')


@never_cache
def Login(request):
    if request.user.is_authenticated:
        return redirect('/')
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        request.session['email'] = email
        request.session['password'] = password

        if not email and not password:
            messages.warning(request, 'Enter details to field')
            return redirect('login')

        user = authenticate(request, username=email, password=password)
        if user is not None and user.is_active:
            request.session['verification_type'] = 'login'
            send_otp(request)
            return redirect('otp_page')
        else:
            messages.error(request, 'Invalid username or password')
            return redirect('login')
    return render(request, "login.html")


def profile_change_password(request, uid):
    user = User.objects.get(id=uid)
    email = user.email
    print(email)
    request.session['email'] = email
    request.session['verification_type'] = 'profile_password_change'
    send_otp(request)
    return redirect('otp_page')


@never_cache
def otp_page(request):
    email = request.session['email']
    return render(request, 'otp.html', {"email": email})


@never_cache
def otp_verification(request):
    if request.method == 'POST':
        otp1 = request.POST.get('otp1', '')
        otp2 = request.POST.get('otp2', '')
        otp3 = request.POST.get('otp3', '')
        otp4 = request.POST.get('otp4', '')
        entered_otp = otp1 + otp2 + otp3 + otp4
        otp_sent = request.session.get('otp')
        verification_type = request.session.get('verification_type')

        if entered_otp == otp_sent:
            username = request.session.get('username')
            email = request.session.get('email')
            password = request.session.get('password')

            if verification_type == 'register':
                user = User.objects.create_user(username=username, email=email, password=password)
                user.save()

                referral_code = generate_referral_code()
                code = user.username + referral_code
                referral = Reffer(user=user, code=code)
                referral.save()

                entered_referral_code = request.session.get('code')
                if entered_referral_code:
                    try:
                        existing_referral = Reffer.objects.get(code=entered_referral_code)
                        referring_user = existing_referral.user
                        print(referring_user)

                        try:
                            user_wallet = Wallet.objects.get(user=referring_user)
                            user_wallet.amount += 100
                            user_wallet.save()



                        except Wallet.DoesNotExist:
                            user_wallet = Wallet.objects.create(user=referring_user, amount=100)
                        messages.success(request, "Registration successful with referral code.")
                    except Reffer.DoesNotExist:
                        messages.success(request, "Registration successful. You can now log in.")

            elif verification_type == 'login':
                user = authenticate(request, username=email, password=password)
                if user is not None:
                    username = user.username
                    request.session['username'] = username
                    login(request, user)
                    print(user)
                    return redirect('/')
                else:
                    messages.error(request, 'Invalid credentials')
                    return redirect('login')
            elif verification_type == 'forgot_password':
                return redirect('confirm_password')

            elif verification_type == 'profile_password_change':
                return redirect('confirm_password_profile')

            request.session.clear()
            return redirect('login')
        else:
            messages.error(request, "Invalid OTP. Please try again.")
            return render(request, 'otp.html', {"email": request.session.get('email')})

    return render(request, 'login.html')


def generate_referral_code():
    r = ""
    for x in range(0, 4):
        r += str(random.randint(0, 9))
    return ''.join(random.choice(r) for i in range(6))


@never_cache
def confirm_password_profile(request):
    if request.method == "POST":
        password = request.POST.get('password1')
        confirm_password = request.POST.get('password2')

        if password == confirm_password:
            email = request.session.get('email')
            user = User.objects.get(email=email)
            user.set_password(password)
            user.save()
            messages.success(request, 'Password reset successful')
            return redirect('/')
        else:
            messages.warning(request, 'Passwords do not match')
            print('not set')
            return redirect("confirm_password")
    return render(request, 'confirm_password.html')


@never_cache
def send_otp(request):
    s = ""
    for x in range(0, 4):
        s += str(random.randint(0, 9))
    print(s)
    request.session["otp"] = s
    email = request.session.get('email')

    send_mail("otp for sign up", s, 'abhinnandu135@gmail.com', [email], fail_silently=False)
    otp_generated_time = int(time.mktime(datetime.datetime.now().timetuple()) * 1000)

    return render(request, "otp.html", {"email": email, "otpGeneratedTime": otp_generated_time})


@never_cache
def resend_otp(request):
    new_otp = "".join([str(random.randint(0, 9)) for _ in range(4)])
    print(new_otp)
    email = request.session.get('email')
    send_mail("New OTP for Sign Up", new_otp, 'abhinnandu135@gmail.com', [email], fail_silently=False)
    request.session['otp'] = new_otp
    return redirect('otp_page')


# @never_cache
# @login_required
# def Logout(request):
#     if request.method=='POST' :
#         request.session.flush()
#         logout(request)
#         return redirect('home')
#

class CustomLogoutView(View):
    def post(self, request, *args, **kwargs):
        if request.method == 'POST':
            request.session.flush()
            logout(request)
            return redirect('home')


@never_cache
def forgot_password(request):
    if request.user.is_authenticated:
        return redirect('/')

    if request.method == "POST":
        email = request.POST['email']
        if User.objects.filter(email=email).exists():
            request.session['verification_type'] = 'forgot_password'
            request.session['email'] = email
            send_otp(request)
            return redirect('otp_page')
        else:
            messages.error(request, 'Email not registered')
    return render(request, 'password_email_enter.html')


@never_cache
def confirm_password(request):
    if request.user.is_authenticated:
        return redirect('/')
    if request.method == "POST":
        password = request.POST.get('password1')
        confirm_password = request.POST.get('password2')

        if password == confirm_password:
            email = request.session.get('email')
            print(email)
            user = User.objects.get(email=email)
            print(user)
            user.set_password(password)  # to change the password
            user.save()
            print('set')
            messages.success(request, 'Password reset successful')
            return redirect('login')


        else:
            messages.warning(request, 'Passwords do not match')
            print('not set')
            return redirect("confirm_password")
    return render(request, 'confirm_password.html')
