import datetime
import re

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.shortcuts import render, redirect
from cartapp.models import *
from cartapp.views import _cart_id
from django.http import JsonResponse
from .models import *
from django.utils import timezone


# Create your views here.


@login_required(login_url='login')
def checkout(request, total=0, quantity=0, cart_items=None):
    tax=shipping=grand_total=0
    if not 'username' in request.session:
        return redirect('login')
    user = request.user
    try:
        tax = 0
        shipping = 0
        grand_total = 0

        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True,product__soft_delete=False)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True,product__soft_delete=False)

        for cart_item in cart_items:
            total += cart_item.product.price * cart_item.quantity
            quantity += cart_item.quantity

        for cart_item in cart_items:
            if cart_item.variant.quantity < 1:
                return redirect('/')

        tax = (18 * total) / 100
        shipping = 0
        grand_total = total + tax
    except Cart.DoesNotExist:
        pass
    except CartItem.DoesNotExist:
        pass

    if cart_items.count() == 0:
        return redirect('cart')

    address_list = Address.objects.filter(user=request.user)
    sorted_addresses = sorted(address_list, key=lambda x: not x.is_default)

    context = {
        'user': user,
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'tax': tax,
        'shipping': shipping,
        'grand_total': grand_total,
        'address_list': sorted_addresses,
    }
    return render(request, 'user/shop-checkout.html', context)



@login_required
def add_address(request, uid):
    if not 'username' in request.session:
        return redirect('login')
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
            return redirect('checkout')

        if not is_valid_phone(phone):
            messages.error(request, 'Invalid phone number. Please enter a 10-digit numeric phone number.')
            return redirect('checkout')

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
            pincode=pincode
        )

        address.save()
        Address.objects.filter(user=request.user).exclude(id=address.id).update(is_default=False)
        address.is_default = True
        address.save()
        return redirect('checkout')


def is_valid_phone(phone):
    pattern = re.compile(r'^\d{10}$')
    return pattern.match(phone)


@login_required
def place_order(request, total=0, quantity=0):
    if not 'username' in request.session:
        return redirect('login')

    current_user = request.user

    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()
    if cart_count <= 0:
        return redirect('product_list')

    tax = 0
    shipping = 0
    grand_total = 0
    discount = 0

    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity

    for cart_item in cart_items:
        if cart_item.variant.quantity < 1:
            messages.error(request, "Some of your items are out of stock.")
            return redirect('checkout')

    tax = (18 * total) / 100
    shipping = 0
    grand_total = total + tax + shipping

    if request.method == 'POST':
        address_id = request.POST.get('default_address')

        try:
            address = Address.objects.get(id=address_id)
        except Address.DoesNotExist:
            messages.warning(request, "Select a address.")
            return redirect('cart')

        data = Order()
        data.user = current_user
        data.address = address
        data.order_total = grand_total
        data.shipping = shipping
        data.tax = tax
        data.save()

        yr = int(datetime.date.today().strftime('%Y'))
        dt = int(datetime.date.today().strftime('%d'))
        mt = int(datetime.date.today().strftime('%m'))
        d = datetime.date(yr, mt, dt)
        current_date = d.strftime("%Y%m%d")

        order_number = current_date + str(data.id)
        data.order_number = order_number
        data.save()

        order = Order.objects.get(user=current_user, is_ordered=False, order_number=order_number)
        context = {
            'order': order,
            'cart_items': cart_items,
            'total': total,
            'tax': tax,
            'shipping': shipping,
            'discount': discount,
            'grand_total': grand_total,
            'address': address
        }

        return redirect('payments', order_id=order.id)
    else:
        return redirect('checkout')


@login_required
def payments(request, order_id):
    if not 'username' in request.session:
        return redirect('login')
    current_user = request.user
    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()
    order = Order.objects.get(user=current_user, is_ordered=False, id=order_id)
    if cart_count <= 0:
        return redirect('product_list')

    tax = 0
    shipping = 0
    grand_total = 0
    total = 0
    quantity = 0

    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity

    tax = (18 * total) / 100
    shipping = 0
    grand_total = order.order_total

    try:
        address = order.address
    except Order.DoesNotExist:
        return redirect('payments')

    context = {
        'address': address,
        'order': order,
        'cart_items': cart_items,
        'total': total,
        'shipping': shipping,
        'tax': tax,
        'grand_total': grand_total,
    }
    return render(request, 'user/payments.html', context)


def apply_coupon(request):
    if request.method == 'POST':
        coupon_code = request.POST.get('coupon_code')
        order_id = request.POST.get('order_id')
        request.session['coupon_code'] = coupon_code

        try:
            coupon = Coupons.objects.get(coupon_code=coupon_code, un_list=False)
            order = Order.objects.get(id=order_id)

            if coupon.valid_from <= timezone.now() <= coupon.valid_to:
                if order.order_total >= coupon.minimum_amount:
                    if coupon.is_used_by_user(request.user):
                        messages.warning(request, 'Coupon has already been Used')
                        print('Coupon has already been Used')
                    else:
                        updated_total = order.order_total - float(coupon.discount)
                        order.order_total = updated_total
                        order.discount = float(coupon.discount)
                        order.save()

                        # used_coupons = UserCoupons(user=request.user, coupon=coupon, is_used=True)
                        # used_coupons.save()

                        request.session['coupon_discount'] = float(coupon.discount)
                        request.session['applied_coupon_code'] = coupon.coupon_code
                        messages.success(request, 'Coupon successfully added')
                        return redirect('payments', order_id)
                else:
                    messages.warning(request, 'Coupon is not Applicable for Order Total')
            else:
                messages.warning(request, 'Coupon is not Applicable for the current date')
        except ObjectDoesNotExist:
            messages.warning(request, 'Coupon code is Invalid')
            return redirect('payments', order_id)

    return redirect('payments', order_id)


def complete_order(request, order_id):
    if request.method == 'POST':
        selected_payment = request.POST.get('payment_option')

        if selected_payment == 'cash_on_delivery':
            return cash_on_delivery(request, order_id)
        elif selected_payment == 'razorpay':
            return confirm_razorpay_payment(request, order_id)
        else:
            pass


@login_required
def order_confirmed(request, order_id):
    if not 'username' in request.session:
        return redirect('login')
    order_products = OrderProduct.objects.filter(order__user=request.user, order__id=order_id)
    orders = Order.objects.filter(is_ordered=True, id=order_id)

    for order_product in order_products:
        order_product.total = order_product.quantity * order_product.product_price
        order_product.tax = (18 * order_product.total) / 100
        order_product.stotal = order_product.total + order_product.tax


    payments = Payment.objects.filter(orderproduct__order__id=order_id)[:1]

    context = {
        'order_products': order_products,
        'orders': orders,
        'payments': payments,
    }
    return render(request, 'user/order_confirmed.html', context)


@transaction.atomic
def cash_on_delivery(request, order_id):
    current_user = request.user
    try:
        order = Order.objects.get(id=order_id, user=current_user, is_ordered=False)
    except Order.DoesNotExist:
        return redirect('order_confirmed')

    total_amount = order.order_total

    payment = Payment(user=current_user, payment_method="Cash on delivery", amount_paid=total_amount, status="Not Paid")

    payment.save()
    order.is_ordered = True
    order.payment = payment
    order.save()

    cart_items = CartItem.objects.filter(user=current_user)

    for cart_item in cart_items:
        variant = cart_item.variant
        stock = cart_item.variant.quantity - cart_item.quantity
        cart_item.variant.quantity = stock
        size=cart_item.size
        variant.save()

        order_product = OrderProduct(
            order=order,
            payment=payment,
            user=current_user,
            product=cart_item.product,
            quantity=cart_item.quantity,
            product_price=cart_item.product.price,
            ordered=True,
            size=size,
            variant = variant,
        )
        order_product.save()
    cart_items.delete()
    order_products = OrderProduct.objects.filter(order=order)
    wishlist_items = Wishlist.objects.filter(user=current_user, product__in=[order_product.product for order_product in
                                                                     order_products])
    wishlist_items.delete()

    applied_coupon_code = request.session.get('coupon_code')
    if applied_coupon_code:
        try:
            coupon = Coupons.objects.get(coupon_code=applied_coupon_code)
            used_coupons = UserCoupons(user=request.user, coupon=coupon, is_used=True)
            used_coupons.save()
        except Coupons.DoesNotExist:
            pass

    if 'coupon_discount' in request.session:
        del request.session['coupon_discount']

    return redirect('order_confirmed', order_id=order_id)


@transaction.atomic
def confirm_razorpay_payment(request, order_id):
    current_user = request.user
    try:
        order = Order.objects.get(id=order_id, user=current_user, is_ordered=False)
    except Order.DoesNotExist:
        return redirect('order_confirmed')

    total_amount = order.order_total

    payment = Payment(user=current_user, payment_method="Razor pay", amount_paid=total_amount, status="Paid")
    payment.save()
    order.is_ordered = True
    order.payment = payment
    order.save()

    cart_items = CartItem.objects.filter(user=current_user)

    for cart_item in cart_items:
        variant = cart_item.variant
        stock = cart_item.variant.quantity - cart_item.quantity
        cart_item.variant.quantity = stock
        variant.save()
        size = cart_item.size
        order_product = OrderProduct(
            order=order,
            payment=payment,
            user=current_user,
            product=cart_item.product,
            quantity=cart_item.quantity,
            product_price=cart_item.product.price,
            ordered=True,
            size=size,
            variant=variant,
        )
        order_product.save()
    cart_items.delete()
    order_products = OrderProduct.objects.filter(order=order)
    wishlist_items = Wishlist.objects.filter(user=current_user, product__in=[order_product.product for order_product in
                                                                     order_products])
    wishlist_items.delete()

    applied_coupon_code = request.session.get('coupon_code')
    if applied_coupon_code:
        try:
            coupon = Coupons.objects.get(coupon_code=applied_coupon_code)
            used_coupons = UserCoupons(user=request.user, coupon=coupon, is_used=True)
            used_coupons.save()
        except Coupons.DoesNotExist:
            pass

    if 'coupon_discount' in request.session:
        del request.session['coupon_discount']
    return redirect('order_confirmed', order_id=order_id)


@transaction.atomic
def wallet_pay(request, order_id):
    user = request.user
    order = Order.objects.get(id=order_id)
    try:
        wallet = Wallet.objects.get(user=user)

    except:
        wallet = Wallet.objects.create(user=user, amount=0)
        wallet.save()

    if wallet.amount > order.order_total:
        payment = Payment.objects.create(user=user, payment_method='Wallet', amount_paid=order.order_total,
                                         status='Paid')
        payment.save()
        order.is_ordered = True

        order.payment = payment
        order.save()
        wallet.amount -= order.order_total
        wallet.save()

        cart_items = CartItem.objects.filter(user=user)

        for cart_item in cart_items:
            variant = cart_item.variant
            stock = cart_item.variant.quantity - cart_item.quantity
            cart_item.variant.quantity = stock
            variant.save()
            size = cart_item.size
            order_product = OrderProduct(
                order=order,
                payment=payment,
                user=user,
                product=cart_item.product,
                quantity=cart_item.quantity,
                product_price=cart_item.product.price,
                ordered=True,
                size=size,
                variant=variant,
            )
            order_product.save()

        cart_items.delete()
        order_products = OrderProduct.objects.filter(order=order)
        wishlist_items = Wishlist.objects.filter(user=user, product__in=[order_product.product for order_product in
                                                                         order_products])
        wishlist_items.delete()



    else:
        messages.warning(request, 'Not Enough Balance in Wallet')
        return redirect('payments', order_id)

    applied_coupon_code = request.session.get('coupon_code')
    if applied_coupon_code:
        try:
            coupon = Coupons.objects.get(coupon_code=applied_coupon_code)
            used_coupons = UserCoupons(user=request.user, coupon=coupon, is_used=True)
            used_coupons.save()
        except Coupons.DoesNotExist:
            pass
    return redirect('order_confirmed', order_id=order_id)
