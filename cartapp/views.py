import uuid

from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from mainapp.models import *
from .models import *
from django.shortcuts import get_object_or_404, redirect


# Create your views here.



def _cart_id(request):
    if request.user.is_authenticated:
        cart_id = request.session.session_key
        if not cart_id:
            request.session.save()  # Save session to generate a session key
            cart_id = request.session.session_key
    else:
        if 'cart_id' not in request.session:
            request.session['cart_id'] = uuid.uuid4().hex  # Generate a random cart ID for anonymous users
        cart_id = request.session['cart_id']

    return cart_id


def add_cart(request, product_id):
    user = request.user
    product = Products.objects.get(id=product_id)
    if request.method == "POST":
        size_id = request.POST.get("size_id")
        selected_quantity = int(request.POST.get('qty', 1))
        variant = ProductAttribute.objects.get(product=product, size=size_id)
        print(variant)

        if user.is_authenticated:
            try:
                cart = Cart.objects.get(cart_id=_cart_id(request))
            except Cart.DoesNotExist:
                cart = Cart.objects.create(cart_id=_cart_id(request),user=user)
            cart.save()

            try:
                cart_item = CartItem.objects.get(
                    product=product, user=user, size=size_id, variant=variant
                )
                if cart_item:
                    if cart_item.quantity + selected_quantity <= variant.quantity:
                        cart_item.quantity += selected_quantity - 1
                        cart_item.save()

            except CartItem.DoesNotExist:
                cart_item = CartItem.objects.create(
                    product=product,
                    quantity=1,
                    cart=cart,
                    user=request.user,
                    size=size_id,
                    variant=variant
                )
                cart_item.save()
                if cart_item:
                    if cart_item.quantity + selected_quantity <= variant.quantity:
                        cart_item.quantity += selected_quantity - 1
                        cart_item.save()
            return redirect("cart")
        else:
            print('not a user')
            try:
                cart = Cart.objects.get(cart_id=_cart_id(request))
                print(cart)
            except Cart.DoesNotExist:
                cart = Cart.objects.create(cart_id=_cart_id(request),user=None)
                print('cart2',cart)
                cart.save()

            try:
                cart_item = CartItem.objects.get(
                    product=product, cart=cart, size=size_id, variant=variant
                )
                cart_item.quantity += 1
                cart_item.save()

            except ProductAttribute.DoesNotExist:
                # If the product variant doesn't exist
                pass

            except CartItem.DoesNotExist:
                cart_item = CartItem.objects.create(
                    product=product,
                    quantity=1,
                    cart=cart,
                    size=size_id,
                    variant=variant,
                )
                cart_item.save()

            return redirect("cart")


def cart(request, total=0, quantity=0, cart_items=None):
    shp = grand_total = tax = coup = amount = 0
    try:
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True,
                                                 product__soft_delete=False).order_by('-product')
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True, product__soft_delete=False)

        for cart_item in cart_items:
            size = int(cart_item.size)
            if cart_item.quantity > cart_item.variant.quantity:
                cart_item.quantity = cart_item.variant.quantity
                cart_item.save()
                if cart_item.product.quantity < 1:
                    cart_item.delete()
                    return redirect('cart')

            total += cart_item.product.price * cart_item.quantity
            quantity += cart_item.quantity
            tax = (18 * total) / 100
            grand_total = total + tax
    except Cart.DoesNotExist:
        pass
    except CartItem.DoesNotExist:
        pass

    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'tax': tax,
        'grand_total': grand_total,
    }
    return render(request, 'user/cart.html', context)


def cart_plus(request, variant_id):
    variant = get_object_or_404(ProductAttribute, id=variant_id)
    if request.user.is_authenticated:
        cart_item = CartItem.objects.get(variant=variant, user=request.user)
        if cart_item.quantity < variant.quantity:
            cart_item.quantity += 1
        else:
            messages.error(request, "Product out of stock")
            cart_item.quantity = variant.quantity
        cart_item.save()
    else:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_item = CartItem.objects.get(variant=variant, cart=cart)
        if cart_item.quantity < variant.quantity:
            cart_item.quantity += 1
        else:
            cart_item.quantity = variant.quantity
        cart_item.save()
    return redirect("cart")




def remove_cart(request, product_id):
    product = Products.objects.filter(id=product_id).first()

    try:
        if request.user.is_authenticated:
            cart_item = CartItem.objects.filter(product=product, user=request.user).first()
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_item = CartItem.objects.filter(product=product, cart=cart).first()

        if cart_item:
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.save()
            else:
                cart_item.delete()
    except ObjectDoesNotExist:
        pass

    return redirect('cart')


def remove_cart_item(request, product_id):
    product = Products.objects.filter(id=product_id).first()
    if request.user.is_authenticated:
        cart_items = CartItem.objects.filter(product=product, user=request.user)
    else:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_items = CartItem.objects.filter(product=product, cart=cart)

    if cart_items.exists():
        cart_item_to_delete = cart_items.first()
        cart_item_to_delete.delete()

    return redirect('cart')

def add_to_cart_short(request, product_id):
    product = get_object_or_404(Products, id=product_id)
    default_variant = product.productattribute_set.first()

    if default_variant:
        size_id = default_variant.id

        if request.user.is_authenticated:
            try:
                cart = Cart.objects.get(cart_id=_cart_id(request))
            except Cart.DoesNotExist:
                cart = Cart.objects.create(cart_id=_cart_id(request), user=request.user)

            try:
                cart_item = CartItem.objects.get(product=product, user=request.user, size=size_id, variant=default_variant)
                if cart_item:
                    # Increment quantity if the cart item already exists
                    if cart_item.quantity + 1 <= default_variant.quantity:
                        cart_item.quantity += 1
                        cart_item.save()
            except CartItem.DoesNotExist:
                # Create a new cart item if it doesn't exist
                CartItem.objects.create(
                    product=product,
                    quantity=1,
                    cart=cart,
                    user=request.user,
                    size=size_id,
                    variant=default_variant
                )

            return redirect('cart')

    return redirect('wishlist')



















# def _cart_id(request):
#     cart = request.session.session_key
#     if not cart:
#         cart = request.session.session_key
#     return cart