import re
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.db import transaction
from django.forms import FloatField
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from adminapp.models import Offers
from .models import Products
from .decorator import admin_required, user_required
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.db.models import Count, Sum, ExpressionWrapper, F
from cartapp.models import *
from cartapp.views import _cart_id
from orderapp.models import *
from django.db.models import Q
from django.utils import timezone
from datetime import datetime
from django.db.models import Avg


def home(request):
    featured = Products.objects.filter(soft_delete=False).filter(category__soft_delete=False)[:8]
    featured_all = Products.objects.filter(soft_delete=False).filter(category__soft_delete=False)
    new_added = Products.objects.filter(soft_delete=False).filter(category__soft_delete=False).order_by('-created_on')[
                :4]
    new = Products.objects.filter(soft_delete=False).filter(category__soft_delete=False).order_by('-created_on')
    categories = Category.objects.filter(soft_delete=False)

    print(request.user)

    context = {
        'username': request.user.username,
        'featured': featured,
        'new_added': new_added,
        'featured_all': featured_all,
        'new': new,
        'categories': categories,
    }

    if not request.user.is_active:
        request.session.flush()
        print('blocked')
    return render(request, 'index.html', context)


def product_list(request):
    query = request.GET.get('search')
    category = Category.objects.filter(soft_delete=False)
    unique_brands = Products.objects.filter(soft_delete=False).values('brand_name').distinct()
    unique_sizes = ProductAttribute.objects.values_list('size', flat=True).distinct()
    unique_sizes = sorted(unique_sizes, key=lambda x: int(x))
    unique_colors = Products.objects.values_list('colors', flat=True).distinct()

    selected_categories = request.GET.getlist('category')
    selected_brands = request.GET.getlist('brand')
    selected_sizes = list(map(int, request.GET.getlist('size')))
    selected_colors = request.GET.getlist('color')
    print(selected_sizes)

    filters = Q()

    if selected_categories:
        filters &= Q(category__id__in=selected_categories)

    products = Products.objects.filter(soft_delete=False, category__soft_delete=False)

    if selected_brands:
        filters &= Q(brand_name__in=selected_brands)

    if selected_sizes:
        filters &= Q(productattribute__size__in=selected_sizes)

    if selected_colors:
        filters &= Q(colors__in=selected_colors)

    if query:
        products = products.filter(
            Q(product_name__icontains=query) |
            Q(category__category_name__icontains=query)
        )

    products = products.filter(filters)

    # products=Products.objects.all()

    paginator = Paginator(products, 8)
    total_items = products.count()

    page_number = request.GET.get('page', 1)
    try:
        page = paginator.page(page_number)
    except (EmptyPage, InvalidPage):
        page = paginator.page(1)

    context = {
        'products': page,
        'total_items': total_items,
        'query': query,
        'category': category,
        'unique_brands': unique_brands,
        'unique_sizes': unique_sizes,
        'unique_colors': unique_colors,
        'selected_sizes': selected_sizes,
        'selected_colors': selected_colors,
        'selected_categories': selected_categories,
        'selected_brands': selected_brands,

    }
    return render(request, 'product/product_list.html', context)


def product(request, p_id, has_offer=False, average_rating=0):
    my_review = None
    has_ordered = False
    existing_review = None
    average_rating = 0
    product = Products.objects.get(id=p_id)
    variant_sizes = ProductAttribute.objects.filter(product=product, quantity__gt=0).values_list('size',
                                                                                                 flat=True).distinct()
    variant_sizes_count = ProductAttribute.objects.filter(product=product, quantity__gt=0).values_list('size',
                                                                                                       flat=True).distinct().count()
    reviews = Reviews.objects.filter(product=product)
    count = Reviews.objects.filter(product=product).count()

    try:
        average_rating = reviews.aggregate(Avg('rating'))['rating__avg']
        if average_rating:
            product.rating = average_rating
            product.save()
    except ObjectDoesNotExist:
        pass

        # user image
    review_with_images = []
    for review in reviews:
        user_id = review.user_id
        user_profile = Profile.objects.filter(user_id=user_id).first()
        if user_profile:
            profile_image_url = user_profile.profile_image.url
            review_with_images.append((review, profile_image_url))

    if request.user.is_authenticated:
        has_ordered = OrderProduct.objects.filter(order__user=request.user, product=product, ordered=True).exists()
        existing_review = Reviews.objects.filter(user=request.user, product=product).exists()

        # logined user review
        try:
            my_review = Reviews.objects.get(user=request.user, product=product)
            print(my_review.comment)
        except ObjectDoesNotExist:
            pass

    # offer management
    old_price_query = Products.objects.filter(id=p_id).values_list('old_price', flat=True)
    old_price = old_price_query[0] if old_price_query else 0
    percentage = 0

    try:
        offer_product = Offers.objects.get(product=product, is_unlisted=False)
        current_datetime = timezone.now()
        if offer_product.valid_from <= current_datetime <= offer_product.valid_to:
            has_offer = True
            discount_value = float(offer_product.discount_value)

            if offer_product.discount_type == 'percentage':
                offer_price = float(old_price) - (float(old_price) * (discount_value / 100))
                product.price = offer_price
                percentage = discount_value
            elif offer_product.discount_type == 'amount':
                offer_price = float(old_price) - discount_value
                if offer_price < 0:
                    product.price = 0
                    percentage = 100
                else:
                    product.price = offer_price
                    percentage = (discount_value / float(old_price)) * 100

            product.save()

    except ObjectDoesNotExist:
        try:
            category = product.category
            current_datetime = timezone.now()
            offer_category = Offers.objects.get(category=category, is_unlisted=False)

            if offer_category.valid_from <= current_datetime <= offer_category.valid_to:
                has_offer = True
                discount_value = float(offer_category.discount_value)

                if offer_category.discount_type == 'percentage':
                    offer_price = float(old_price) - (float(old_price) * (discount_value / 100))
                    product.price = offer_price
                    percentage = discount_value
                elif offer_category.discount_type == 'amount':
                    offer_price = float(old_price) - discount_value
                    product.price = offer_price
                    percentage = (discount_value / float(old_price)) * 100

                product.save()

        except ObjectDoesNotExist:
            product.price = old_price
            product.save()

    # cart
    in_cart = CartItem.objects.filter(cart__cart_id=_cart_id(request), product=product).exists()
    in_wishlist = False
    if request.user.is_authenticated:
        in_wishlist = Wishlist.objects.filter(user=request.user, product=product).exists()

    context = {
        'product': product,
        'in_cart': in_cart,
        'in_wishlist': in_wishlist,
        'has_offer': has_offer,
        'percentage': int(percentage),
        'reviews': reviews,
        'has_ordered': has_ordered,
        'existing_review': existing_review,
        'count': count,
        'my_review': my_review,
        'review_with_images': review_with_images,
        'average_rating': average_rating,
        'variant_sizes': variant_sizes,
        'variant_sizes_count': int(variant_sizes_count),
    }
    return render(request, 'product/product.html', context)


@login_required
def profile(request, uid):
    if not 'username' in request.session:
        return redirect('login')
    user = User.objects.get(id=uid)
    user_orders=Order.objects.filter(user=user,is_ordered=True).count()
    total_spent = Payment.objects.filter(user=user,status='Paid').aggregate(total_amount=Sum('amount_paid'))[
        'total_amount']
    total_spent = total_spent if total_spent is not None else 0.0

    try:
        profile = Profile.objects.get(user=user)
    except Profile.DoesNotExist:
        profile = Profile(user=user)  # Create a new profile if it doesn't exist
        profile.save()

    r = Reffer.objects.get(user=request.user)
    print(r.code)

    context = {
        'user': user,
        'profile': profile,
        'referral_code': r,
        'user_orders':user_orders,
        'total_spent':total_spent,
    }

    return render(request, 'user/profile.html', context)


@login_required
def profile_view(request, uid):
    if not 'username' in request.session:
        return redirect('login')
    user = User.objects.get(id=uid)
    try:
        profile = Profile.objects.get(user=user)
    except Profile.DoesNotExist:
        profile = Profile(user=user)  # Create a new profile if it doesn't exist
        profile.save()

    context = {
        'user': user,
        'profile': profile
    }
    return render(request, 'user/profile-view.html', context)


@login_required
def profile_edit(request, uid):
    if not 'username' in request.session:
        return redirect('login')
    user = User.objects.get(id=uid)
    try:
        profile = Profile.objects.get(user=user)
    except Profile.DoesNotExist:
        profile = Profile(user=user)  # Create a new profile if it doesn't exist
        profile.save()

    if request.method == 'POST':
        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        new_profile_image = request.FILES.get('new_profile_image')
        if new_profile_image:
            profile.profile_image = new_profile_image
            profile.save()

        if username:  # Check if username is not empty
            if User.objects.filter(username=username).exclude(id=uid).exists():
                messages.error(request, 'Username already exists. Please choose a different username.')
            else:
                user.username = username

        user.first_name = first_name
        user.last_name = last_name
        user.save()
        return redirect('profile_view', uid=uid)

    context = {
        'user': user,
        'profile': profile
    }

    return render(request, 'user/profile-edit.html', context)


def delete_user(request):
    if not 'username' in request.session:
        return redirect('login')
    request.user.delete()
    request.session.clear()
    return redirect('home')


@login_required
def profile_address(request, uid):
    if not 'username' in request.session:
        return redirect('login')
    user = User.objects.get(id=uid)
    address_list = Address.objects.filter(user=request.user)
    sorted_addresses = sorted(address_list, key=lambda x: not x.is_default)
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        email = request.POST.get('email', '')
        house_name = request.POST.get('house_name', '')
        phone = request.POST.get('phone', '')
        locality = request.POST.get('locality', '')
        city = request.POST.get('city', '')
        state = request.POST.get('state', '')
        landmark = request.POST.get('landmark', '')
        pincode = request.POST.get('pin', '')

        if not all([first_name, last_name, email, house_name, phone, locality, city, state, landmark, pincode]):
            messages.error(request, 'All fields are required.')
            return redirect('profile_address', uid=uid)

        if not is_valid_phone(phone):
            messages.error(request, 'Invalid phone number. Please enter a 10-digit numeric phone number.')
            return redirect('profile_address', uid=uid)

        address = Address(
            user=request.user,
            first_name=first_name,
            landmark=landmark,
            last_name=last_name,
            phone=phone,
            email=email,
            locality=locality,
            house_name=house_name,
            city=city,
            state=state,
            pincode=pincode,
        )

        address.save()
        Address.objects.filter(user=request.user).exclude(id=address.id).update(is_default=False)
        address.is_default = True
        address.save()

        return redirect('profile_address', uid=uid)

    contetx = {
        'user': user,
        'address': sorted_addresses,
    }
    return render(request, 'user/profile-address.html', contetx)


def is_valid_phone(phone):
    # Define a regular expression for a 10-digit numeric phone number
    pattern = re.compile(r'^\d{10}$')
    return pattern.match(phone)


@login_required
def profile_edit_address(request, uid, address_id):
    if not 'username' in request.session:
        return redirect('login')
    user = User.objects.get(id=uid)
    try:
        address = Address.objects.get(id=address_id, user=request.user)
    except Address.DoesNotExist:
        return HttpResponse("Invalid Address ID")

    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        locality = request.POST.get('locality')
        landmark = request.POST.get('landmark')
        house_name = request.POST.get('house_name')
        city = request.POST.get('city')
        state = request.POST.get('state')
        pincode = request.POST.get('pin')

        address.first_name = first_name
        address.last_name = last_name
        address.phone = phone
        address.email = email
        address.locality = locality
        address.landmark = landmark
        address.house_name = house_name
        address.city = city
        address.state = state
        address.pincode = pincode
        address.save()
        return redirect('profile_address', uid=uid)

    context = {
        'user': user,
        'address': address,
    }
    return render(request, 'user/profile-edit-address.html', context)


def make_default_address(request, uid, address_id):
    address = get_object_or_404(Address, id=address_id, user_id=uid)

    Address.objects.filter(user_id=uid, is_default=True).update(is_default=False)
    address.is_default = True
    address.save()

    return redirect('profile_address', uid=uid)


@login_required(login_url='login')
def delete_address(request, uid, address_id):
    if not 'username' in request.session:
        return redirect('login')
    try:
        address = Address.objects.get(id=address_id, user=request.user)
        is_default = address.is_default

        address.delete()
        if is_default:
            new_default_address = Address.objects.filter(user=request.user).exclude(id=address_id).order_by(
                '-id').first()

            if new_default_address:
                new_default_address.is_default = True
                new_default_address.save()

    except Address.DoesNotExist:
        return HttpResponse("Invalid Address ID")

    return redirect('profile_address', uid=uid)



def profile_orders(request):
    if not 'username' in request.session:
        return redirect('login')
    orders = Order.objects.filter(user=request.user, is_ordered=True)
    order_products_list = OrderProduct.objects.filter(order__user=request.user).order_by('-created_at')
    paginator = Paginator(order_products_list, 8)

    try:
        page = int(request.GET.get('page', 1))
    except ValueError:
        page = 1
    try:
        order_products = paginator.page(page)
    except (EmptyPage, InvalidPage):
        order_products = paginator.page(paginator.num_pages)
    context = {
        'orders': orders,
        'order_products': order_products,
    }
    return render(request, 'user/profile_orders.html', context)


@login_required(login_url='login')
def profile_order_view(request, order_id):
    global context
    order_products = OrderProduct.objects.filter(order__user=request.user, order__id=order_id)
    orders = Order.objects.filter(is_ordered=True, id=order_id)

    payments = Payment.objects.filter(orderproduct__order__id=order_id)[:1]

    for order_product in order_products:
        order_product.total = order_product.quantity * order_product.product_price
    context = {
        'order_products': order_products,
        'orders': orders,
        'payments': payments,
    }
    return render(request, 'user/profile_order_view.html', context)


def cancel_order(request, order_id):
    if 'username' not in request.session:
        return redirect('login')
    try:
        order = Order.objects.select_related('user').get(id=order_id, user=request.user)
        payment_methods = []
        try:
            payments = Payment.objects.filter(orderproduct__order=order)
            for payment in payments:
                payment_methods.append(payment.payment_method)
        except Payment.DoesNotExist:
            pass
        except MultipleObjectsReturned:
            pass
        if order.status in ["New", "Accepted"]:
            if "Razor pay" in payment_methods or "Wallet" in payment_methods:
                user_wallet = Wallet.objects.get_or_create(user=request.user)[0]
                user_wallet.amount += order.order_total
                user_wallet.save()

            order.status = "Cancelled"
            order.save()

            for order_product in order.orderproduct_set.all():
                variant = order_product.variant
                variant.quantity += order_product.quantity  # Increase the quantity
                variant.save()
    except Order.DoesNotExist:
        pass

    return redirect('profile_orders')
@login_required(login_url='login')
def return_order(request, order_id):
    try:
        order = Order.objects.select_related('user').get(id=order_id, user=request.user)
        payment_methods = []
        try:
            payments = Payment.objects.filter(orderproduct__order=order)
            for payment in payments:
                payment_methods.append(payment.payment_method)
        except Payment.DoesNotExist:
            pass
        except MultipleObjectsReturned:
            pass
        if order.status == "Delivered":
            if "Razor pay" in payment_methods or "Wallet" in payment_methods:
                user_wallet = Wallet.objects.get_or_create(user=request.user)[0]
                user_wallet.amount += order.order_total
                user_wallet.save()

            order.status = "Returned"
            order.save()

            for order_product in order.orderproduct_set.all():
                product = order_product.product
                product.quantity += order_product.quantity  # Increase the quantity
                product.save()
    except Order.DoesNotExist:
        pass
    return redirect('profile_orders')

@login_required(login_url='login')
def add_to_wishlist(request, product_id):
    product = get_object_or_404(Products, id=product_id)
    user = request.user

    referring_url = request.META.get('HTTP_REFERER', None)
    in_wishlist = Wishlist.objects.filter(user=user, product=product).exists()

    if not in_wishlist:
        Wishlist.objects.create(user=user, product=product)

    redirect_url = referring_url if referring_url else reverse('home')
    return redirect(redirect_url)


def view_wishlist(request):
    if not 'username' in request.session:
        return redirect('login')
    user = request.user

    wishlist_items = Wishlist.objects.filter(user=user)
    wishlist_products = [item.product for item in wishlist_items]

    return render(request, 'user/wishlist.html', {'wishlist_products': wishlist_products})


def remove_from_wishlist(request, product_id):
    if not 'username' in request.session:
        return redirect('login')
    user = request.user
    product = get_object_or_404(Products, id=product_id)

    try:
        wishlist_item = Wishlist.objects.get(user=user, product=product)
        wishlist_item.delete()
        messages.success(request, 'Product removed from wishlist.')
    except Wishlist.DoesNotExist:
        messages.warning(request, 'Product was not in your wishlist.')

    referring_url = request.META.get('HTTP_REFERER', None)

    redirect_url = referring_url if referring_url else reverse('home')
    return redirect(redirect_url)


def my_coupons(request):
    if not 'username' in request.session:
        return redirect('login')
    all_coupons = Coupons.objects.filter(un_list=False)

    # Get used coupons by the logged-in user
    used_coupons = UserCoupons.objects.filter(user=request.user, is_used=True)
    used_coupon_ids = used_coupons.values_list('coupon_id', flat=True)

    # Get used coupon objects
    used_coupon_objects = all_coupons.filter(id__in=used_coupon_ids)

    # Filter out expired coupons from available coupons
    current_time = timezone.now()
    available_coupons = all_coupons.exclude(id__in=used_coupon_ids).filter(valid_to__gt=current_time)

    # Get expired coupons
    expired_coupons = all_coupons.exclude(id__in=used_coupon_ids).filter(valid_to__lt=current_time)
    print(expired_coupons)

    # Merge expired coupons with used coupons for displaying
    used_coupon_objects = used_coupon_objects.union(expired_coupons)
    print(used_coupon_objects)

    context = {
        'used_coupons': used_coupon_objects,
        'available_coupons': available_coupons,
    }

    return render(request, 'user/my_coupons.html', context)


def my_wallet(request):
    if not 'username' in request.session:
        return redirect('login')
    current_user = request.user
    try:
        wallet = Wallet.objects.get(user=current_user)
    except Wallet.DoesNotExist:
        wallet = Wallet.objects.create(user=current_user, amount=0)
    wallet_amount = wallet.amount

    context = {'wallet_amount': wallet_amount}

    return render(request, 'user/profile-wallet.html', context)


def add_review(request, p_id):
    if not 'username' in request.session:
        return redirect('login')
    product = get_object_or_404(Products, id=p_id)
    user = request.user
    existing_review = Reviews.objects.filter(user=user, product=product).exists()

    if request.method == 'POST' and not existing_review:
        comment = request.POST.get('comment')
        star = request.POST.get('rating')
        print(star)
        if comment:
            review = Reviews(user=user, product=product, comment=comment, rating=star)
            review.save()
    return redirect('product_detail', p_id=p_id)


def edit_review(request, review_id):
    if not 'username' in request.session:
        return redirect('login')
    review = get_object_or_404(Reviews, pk=review_id)
    user = request.user

    if user == review.user:
        if request.method == 'POST':
            comment = request.POST.get('comment')
            star = request.POST.get('rating')
            review.comment = comment
            review.rating = star
            review.save()
            return redirect('product_detail', p_id=review.product.id)


def delete_review(request, review_id):
    if not 'username' in request.session:
        return redirect('login')
    review = get_object_or_404(Reviews, pk=review_id)
    review.delete()
    return redirect('product_detail', p_id=review.product.id)


def contact(request):
    return render(request, 'user/contact.html')


def about(request):
    return render(request, 'user/about.html')


def custom_404(request, exception):
    return render(request, '404page.html', status=404)


def invoice(request):
    return render(request, 'invoice.html')


def eg(request):
    return render(request, 'eg.html')
