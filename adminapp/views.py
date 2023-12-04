from dateutil.relativedelta import relativedelta
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import MultipleObjectsReturned
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.shortcuts import render, redirect, get_object_or_404
from mainapp.models import *
from django.contrib.auth.models import User
from django.db.models import Count, Q
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.utils import timezone
from orderapp.models import Order, OrderProduct, Payment, Coupons, UserCoupons
from datetime import datetime, timedelta, time
from django.db.models import F, Sum, Count
from .models import *
from datetime import datetime
from .forms import ProductAttributeForm


def admin_home(request):
    if not request.user.is_superuser:
        return redirect('admin_login')

    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)

    total_ordered_orders = Order.objects.filter(is_ordered=True).count()
    total_available_products = Products.objects.filter(soft_delete=False).filter(category__soft_delete=False).count()
    total_available_customer = User.objects.filter(is_superuser=False).count()
    total_available_category = Category.objects.filter(soft_delete=False).count()
    print(total_available_category)
    total_pending = Order.objects.filter(is_ordered=True, status='New').count()
    total_delivered = Order.objects.filter(is_ordered=True, status='Delivered').count()
    total_cancelled = Order.objects.filter(is_ordered=True, status='Cancelled').count()
    total_returned = Order.objects.filter(is_ordered=True, status='Returned').count()

    total_earned_amount = \
        Order.objects.filter(is_ordered=True).exclude(status__in=['Cancelled', 'Returned']).aggregate(
            Sum('order_total'))[
            'order_total__sum'] or 0
    users = User.objects.filter(is_superuser=False)[:5]

    daily_order_counts = (
        Order.objects
        .filter(created_at__range=(start_date, end_date), is_ordered=True)
        .values('created_at__date')
        .annotate(order_count=Count('id'))
        .order_by('created_at__date')
    )

    dates = [entry['created_at__date'].strftime('%Y-%m-%d') for entry in daily_order_counts]
    counts = [entry['order_count'] for entry in daily_order_counts]

    orders = Order.objects.filter(is_ordered=True).order_by('-created_at')[:10]
    context = {
        'username': request.session.get('admin'),
        'total_ordered_orders': total_ordered_orders,
        'total_available_products': total_available_products,
        'total_earned_amount': total_earned_amount,
        'total_available_customer': total_available_customer,
        'total_available_category': total_available_category,
        'total_pending': total_pending,
        'total_returned': total_returned,
        'total_cancelled': total_cancelled,
        'total_delivered': total_delivered,

        'users': users,
        'orders': orders,
        'dates': dates,
        'counts': counts,
        # 'monthly_dates': monthly_dates,
        # 'monthly_counts': monthly_counts,

    }
    return render(request, 'admin/admin_home.html', context)


def admin_login(request):
    if request.user.is_superuser:
        return redirect('admin_home')
    if request.method == 'POST':
        uname = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(username=uname, password=password)

        if user is not None and user.is_superuser and user.is_active:
            request.session['admin'] = uname
            request.session['is_admin'] = True
            login(request, user)
            print(user)
            return redirect('admin_home')
        else:
            messages.error(request, "Invalid credentials. Please Try again.")
            return redirect('admin_login')
    return render(request, 'admin/admin_login.html')


def add_product(request):
    if not request.user.is_superuser:
        return redirect('admin_login')

    cat = Category.objects.all()

    if request.method == 'POST':
        product_name = request.POST.get('product_name')
        brand_name = request.POST.get('brand_name')
        old_price = request.POST.get('old_price')
        price = request.POST.get('price')
        description = request.POST.get('description')
        image1 = request.FILES.get('image1')
        image2 = request.FILES.get('image2')
        image3 = request.FILES.get('image3')
        image4 = request.FILES.get('image4')
        image5 = request.FILES.get('image5')

        material = request.POST.get('material')
        special_feature = request.POST.get('features')
        fit_type = request.POST.get('fit_type')
        shoe_width = request.POST.get('shoe_width')

        category_id = request.POST.get('category')

        color = request.POST.get('colors')

        if not (
                product_name and brand_name and old_price and price and description and color and image1 and image2 and image3 and image4 and image5 and material and special_feature):
            messages.error(request, "Please provide all required fields.")
            return redirect('add_product')

        if not (price.isdigit() and old_price.isdigit() and int(price) >= 0 and int(old_price) >= 0):
            messages.error(request, "Please enter valid prices.")
            return redirect('add_product')

        if int(price) > int(old_price):
            messages.error(request, "Offer price cannot be greater than the original price.")
            return redirect('add_product')

        try:
            category = Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            messages.error(request, "Invalid category selected.")
            return redirect('add_product')

        product = Products(
            product_name=product_name,
            brand_name=brand_name,
            old_price=old_price,
            price=price,
            description=description,
            product_image1=image1,
            product_image2=image2,
            product_image3=image3,
            product_image4=image4,
            product_image5=image5,
            category=category,
            colors=color,
            material=material,
            special_feature=special_feature,
            fit_type=fit_type,
            shoe_width=shoe_width,
        )

        product.save()
        print(product)
        return redirect('admin_products_list')

    return render(request, 'admin/add_product.html', {'category': cat})


def admin_products_list(request):
    if not request.user.is_superuser:
        return redirect('admin_login')

    category_filter = request.GET.get('category', 'All category')
    status_filter = request.GET.get('status', 'Show all')
    products_list = Products.objects.all().order_by('-created_on')

    # Apply category filter
    if category_filter != 'All category':
        products_list = products_list.filter(category__category_name=category_filter)

    # Apply status filter
    if status_filter == 'Active':
        products_list = products_list.filter(soft_delete=False)
    elif status_filter == 'Disabled':
        products_list = products_list.filter(soft_delete=True)

    paginator = Paginator(products_list, 5)

    try:
        page = int(request.GET.get('page', 1))
    except ValueError:
        page = 1

    try:
        products = paginator.page(page)
    except (EmptyPage, InvalidPage):
        products = paginator.page(paginator.num_pages)

    categories = ['All category'] + list(Products.objects.values_list('category__category_name', flat=True).distinct())

    return render(request, 'admin/admin_products_list.html', {
        'products': products,
        'categories': categories,
        'selected_category': category_filter,
        'selected_status': status_filter,
    })


def edit_products(request, p_id):
    if not request.user.is_superuser:
        return redirect('admin_login')
    product = Products.objects.get(id=p_id)
    cat = Category.objects.all()

    if request.method == 'POST':
        product_name = request.POST.get('product_name')
        brand_name = request.POST.get('brand_name')
        old_price = request.POST.get('old_price')
        price = request.POST.get('price')
        description = request.POST.get('description')
        image1 = request.FILES.get('image1')
        image2 = request.FILES.get('image2')
        image3 = request.FILES.get('image3')
        image4 = request.FILES.get('image4')
        image5 = request.FILES.get('image5')
        quantity = request.POST.get('quantity')
        material = request.POST.get('material')
        special_feature = request.POST.get('features')
        fit_type = request.POST.get('fit_type')
        shoe_width = request.POST.get('shoe_width')

        category_id = request.POST.get('category')
        category = Category.objects.get(id=category_id)

        color = request.POST.get('colors')
        sizes = request.POST.get('sizes')

        product.product_name = product_name
        product.brand_name = brand_name
        product.old_price = old_price
        product.price = price
        product.description = description

        # Handle image uploads
        if image1:
            product.product_image1 = image1

        if image2:
            product.product_image2 = image2

        if image3:
            product.product_image3 = image3

        if image4:
            product.product_image4 = image4

        if image5:
            product.product_image5 = image5

        # if not (
        #         product_name and brand_name and old_price and price and description and quantity and color and image1 and image2 and image3 and image4 and image5 and material and special_feature and sizes):
        #     messages.error(request, "Please provide all required fields.")
        #
        #
        # if not (price.isdigit() and old_price.isdigit() and int(price) >= 0 and int(old_price) >= 0):
        #     messages.error(request, "Please enter valid prices.")
        #
        #
        # if int(price) > int(old_price):
        #     messages.error(request, "Offer price cannot be greater than the original price.")
        #
        #
        # try:
        #     category = Category.objects.get(id=category_id)
        # except Category.DoesNotExist:
        #     messages.error(request, "Invalid category selected.")
        #

        product.quantity = quantity
        product.category = category
        product.colors = color
        product.sizes = sizes
        product.material = material
        product.special_feature = special_feature
        product.fit_type = fit_type
        product.shoe_width = shoe_width

        product.save()

        return redirect('admin_products_list')

    return render(request, 'admin/edit_products.html', {'product': product, 'category': cat})


def soft_delete_product(request, d_id):
    product = Products.objects.get(id=d_id)
    product.soft_delete_product()
    return redirect('admin_products_list')


def undo_soft_delete_product(request, d_id):
    product = Products.objects.get(id=d_id)
    product.soft_delete = False
    product.save()
    return redirect('admin_products_list')



def add_categories(request):
    if not request.user.is_superuser:
        return redirect('admin_login')
    categories_list = Category.objects.all().order_by('category_name')
    paginator = Paginator(categories_list, 5)
    if request.method == 'POST':
        cat_name = request.POST.get('category_name')
        cat_image = request.FILES.get('category_image')
        cat_desc = request.POST.get('category_description')
        if not (cat_desc and cat_image and cat_name):
            messages.error(request, "Please provide all required fields.")
            return redirect('add_categories')

        if Category.objects.filter(category_name=cat_name).exists():
            messages.error(request, "Category already exist")
            return redirect('add_categories')

        category = Category(
            category_name=cat_name,
            category_image=cat_image,
            category_desc=cat_desc
        )
        category.save()
        print(category)
    try:
        page = int(request.GET.get('page', 1))
    except:
        page = 1
    try:
        categories = paginator.page(page)
    except (EmptyPage, InvalidPage):
        categories = paginator.page(paginator.num_pages)
    return render(request, 'admin/add_categories.html', {'categories': categories})


def edit_categories(request, c_id):
    if not request.user.is_superuser:
        return redirect('admin_login')
    categories_list = Category.objects.all().order_by('category_name')
    paginator = Paginator(categories_list, 5)
    category = Category.objects.get(id=c_id)

    if request.method == 'POST':
        cat_name = request.POST.get('category_name')
        cat_desc = request.POST.get('category_description')

        if 'category_image' in request.FILES:
            cat_image = request.FILES.get('category_image')
            category.category_image = cat_image

        category.category_name = cat_name
        category.category_desc = cat_desc
        category.save()
        return redirect('add_categories')
    try:
        page = int(request.GET.get('page', 1))
    except:
        page = 1
    try:
        categories = paginator.page(page)
    except (EmptyPage, InvalidPage):
        categories = paginator.page(paginator.num_pages)
    return render(request, 'admin/edit_categories.html', {'category': category, 'categories': categories})


def soft_delete_category(request, c_id):
    category = Category.objects.get(id=c_id)
    category.soft_delete_category()
    return redirect('add_categories')


def undo_soft_delete_category(request, c_id):
    category = Category.objects.get(id=c_id)
    category.soft_delete = False
    category.save()
    return redirect('add_categories')


def user_list(request):
    if not request.user.is_superuser:
        return redirect('admin_login')
    customers_list = User.objects.filter(is_superuser=False).order_by('username')
    paginator = Paginator(customers_list, 10)
    try:
        page = int(request.GET.get('page', 1))
    except:
        page = 1
    try:
        customers = paginator.page(page)
    except (EmptyPage, InvalidPage):
        customers = paginator.page(paginator.num_pages)
    return render(request, 'admin/user_list.html', {'customers': customers})


def block_user(request, u_id):
    user = User.objects.get(id=u_id)
    if not user.is_superuser:
        user.is_active = False
        user.save()
        print(user.is_active)
        if request.user.is_authenticated and request.user.id == user.id:
            logout(request)
    return redirect('user_list')


def unblock_user(request, u_id):
    try:
        user = User.objects.get(id=u_id)
        user.is_active = True
        user.save()
        print(user.is_active)
    except User.DoesNotExist:
        return redirect('user_list')

    return redirect('user_list')


def order_list(request):
    selected_status = request.GET.get('status', 'all')
    search_query = request.GET.get('search', '')

    if selected_status == 'all':
        orders_list = Order.objects.filter(is_ordered=True, user__username__icontains=search_query).order_by(
            '-created_at')
    else:
        orders_list = Order.objects.filter(is_ordered=True, status=selected_status,
                                           user__username__icontains=search_query).order_by('-created_at')

    paginator = Paginator(orders_list, 10)

    try:
        page = int(request.GET.get('page', 1))
    except ValueError:
        page = 1

    try:
        orders = paginator.page(page)
    except (EmptyPage, InvalidPage):
        orders = paginator.page(paginator.num_pages)

    context = {
        'orders': orders,
        'selected_status': selected_status,
        'search_query': search_query,
    }

    return render(request, 'admin/order_list.html', context)


def order_detail(request, order_id):
    order = Order.objects.get(id=order_id, is_ordered=True)
    order_products = OrderProduct.objects.filter(order=order)

    for order_product in order_products:
        order_product.total = order_product.quantity * order_product.product_price
        order_product.tax = (18 * order_product.total) / 100
        order_product.stotal = order_product.total + order_product.tax

    context = {
        'order': order,
        'order_products': order_products,
    }
    return render(request, 'admin/orders-detail.html', context)


@login_required
def update_order_status(request, order_id, new_status):
    order = Order.objects.get(id=order_id, is_ordered=True)
    order_products = OrderProduct.objects.filter(order=order)

    if new_status == 'New':
        order.status = 'New'
    elif new_status == 'Cancelled':
        order.status = 'Cancelled'
        payment_methods = Payment.objects.filter(orderproduct__order=order).values_list('payment_method', flat=True)
        if 'Wallet' in payment_methods or 'Razor pay' in payment_methods:
            user_wallet, created = Wallet.objects.get_or_create(user=order.user)
            user_wallet.amount += order.order_total
            user_wallet.save()

            for order_product in order.orderproduct_set.all():
                variant = order_product.variant
                variant.quantity += order_product.quantity  # Increase the quantity
                variant.save()

    elif new_status == 'Delivered':
        for order_product in order_products:
            if order_product.payment.payment_method == 'Cash on delivery' and order_product.payment.status == 'Not Paid':
                order_product.payment.status = 'Paid'
                order_product.payment.save()
        order.status = new_status
        order.save()

    elif new_status == 'Returned':
        for order_product in order_products:
            if order_product.payment.payment_method == 'Cash on delivery' and order_product.payment.status == 'Not Paid':
                order_product.payment.status = 'Paid'
                order_product.payment.save()
        order.status = new_status
        payments = Payment.objects.filter(orderproduct__order=order, payment_method__in=['Razor pay', 'Wallet'])
        for payment in payments:
            user_wallet, created = Wallet.objects.get_or_create(user=order.user)
            user_wallet.amount += order.order_total
            user_wallet.save()

        for order_product in order.orderproduct_set.all():
            variant = order_product.variant
            variant.quantity += order_product.quantity  # Increase the quantity
            variant.save()

    order.save()
    return redirect('order_detail', order_id=order_id)


def admin_logout(request):
    if not request.user.is_superuser:
        return redirect('admin_login')
    if request.user.is_superuser:
        request.session.flush()
        logout(request)
        return redirect('admin_login')
    else:
        messages.info(request, "Please log in as admin")
        return render(request, 'admin_login.html')


def sales(request):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    total_sales = Order.objects.filter(status='Delivered', created_at__range=(start_date, end_date)).aggregate(
        total_sales=Sum('order_total'))['total_sales'] or 0

    total_orders = Order.objects.filter(created_at__range=(start_date, end_date)).count()
    success_orders = Order.objects.filter(status='Delivered', created_at__range=(start_date, end_date)).count()
    average_order_value = total_sales / success_orders if success_orders != 0 else 0
    delivered_products = OrderProduct.objects.filter(order__status='Delivered',
                                                     order__created_at__range=(start_date, end_date), ordered=True
                                                     ).values('product__product_name'
                                                              ).annotate(total_quantity_sold=Sum('quantity'),
                                                                         total_revenue=Sum(
                                                                             F('quantity') * F('product_price'))
                                                                         # Calculate total revenue here using F expressions
                                                                         ).order_by('-total_quantity_sold')

    order_products = Order.objects.filter(status='Delivered', created_at__range=(start_date, end_date)).order_by(
        '-created_at')
    Month = end_date.month
    print(Month)

    context = {
        'total_sales': total_sales,
        'total_orders': total_orders,
        'average_order_value': average_order_value,
        'delivered_products': delivered_products,
        'end_date': end_date,
        'order_products': order_products,
        'success_orders': success_orders,
        'month': Month
    }

    return render(request, 'admin/monthly_sales.html', context)


def today_sales(request):
    current_datetime = datetime.now()
    current_day = current_datetime.strftime('%d')

    start_date = datetime.combine(current_datetime.date(), time.min)
    end_date = current_datetime

    total_sales = Order.objects.filter(status='Delivered', created_at__range=(start_date, end_date)).aggregate(
        total_sales=Sum('order_total'))['total_sales'] or 0
    total_orders = Order.objects.filter(created_at__range=(start_date, end_date)).count()
    success_orders = Order.objects.filter(status='Delivered', created_at__range=(start_date, end_date)).count()
    average_order_value = total_sales / success_orders if success_orders != 0 else 0

    delivered_products = OrderProduct.objects.filter(order__status='Delivered',
                                                     order__created_at__range=(start_date, end_date), ordered=True
                                                     ).values('product__product_name'
                                                              ).annotate(total_quantity_sold=Sum('quantity'),
                                                                         total_revenue=Sum(
                                                                             F('quantity') * F('product_price'))
                                                                         ).order_by('-total_quantity_sold')

    order_products = Order.objects.filter(status='Delivered', created_at__range=(start_date, end_date)).order_by(
        '-created_at')

    context = {
        'total_sales': total_sales,
        'total_orders': total_orders,
        'success_orders': success_orders,
        'average_order_value': average_order_value,
        'delivered_products': delivered_products,
        'current_datetime': current_datetime,
        'current_day': current_day,
        'order_products': order_products,
    }
    return render(request, 'admin/today_sales.html', context)


def current_year_sales(request):
    current_year = datetime.now().year
    start_date = datetime(current_year, 1, 1)
    end_date = datetime.now()

    total_sales = Order.objects.filter(status='Delivered', created_at__range=(start_date, end_date)
                                       ).aggregate(total_sales=Sum('order_total'))['total_sales'] or 0

    total_orders = Order.objects.filter(created_at__range=(start_date, end_date)).count()
    success_orders = Order.objects.filter(status='Delivered', created_at__range=(start_date, end_date)).count()
    average_order_value = total_sales / success_orders if success_orders != 0 else 0

    delivered_products = OrderProduct.objects.filter(order__status='Delivered',
                                                     order__created_at__range=(start_date, end_date),
                                                     ).values('product__product_name'
                                                              ).annotate(total_quantity_sold=Sum('quantity'),
                                                                         total_revenue=Sum(
                                                                             F('quantity') * F('product_price'))
                                                                         # Calculate total revenue using F expressions
                                                                         ).order_by('-total_quantity_sold')

    order_products = Order.objects.filter(status='Delivered', created_at__range=(start_date, end_date)).order_by(
        '-created_at')

    context = {
        'total_sales': total_sales,
        'total_orders': total_orders,
        'success_orders': success_orders,
        'average_order_value': average_order_value,
        'delivered_products': delivered_products,
        'current_year': current_year,
        'order_products': order_products,
    }

    return render(request, 'admin/current_year_sales.html', context)


def coupon_list(request):
    search_query = request.GET.get('search')
    coupons = Coupons.objects.all().order_by('-valid_to')
    if search_query:
        coupons = coupons.filter(Q(coupon_code__icontains=search_query))
    context = {'coupons': coupons}
    return render(request, 'admin/coupon.html', context)


@login_required
def add_coupons(request):
    if request.method == 'POST':
        coupon_code = request.POST.get('coupon_code')
        description = request.POST.get('description')
        minimum_amount = request.POST.get('minimum_amount')
        discount = request.POST.get('discount')
        valid_from = request.POST.get('valid_from')
        valid_to = request.POST.get('valid_to')

        # Check for empty fields
        if not (coupon_code and description and minimum_amount and discount and valid_from and valid_to):
            messages.error(request, "All fields are required.")
            return redirect('add_coupons')

        try:
            minimum_amount = int(minimum_amount)
            discount = int(discount)
        except ValueError:
            messages.error(request, "Minimum Amount and Discount must be integers.")
            return redirect('add_coupons')

        # Check if discount is greater than minimum amount
        if discount > minimum_amount:
            messages.error(request, "Discount cannot be greater than Minimum Amount.")
            return redirect('add_coupons')

        if valid_from > valid_to:
            messages.error(request, "Valid From date should not be greater than Valid To date.")
            return redirect('add_coupons')

        coupon = Coupons(
            coupon_code=coupon_code,
            description=description,
            minimum_amount=minimum_amount,
            discount=discount,
            valid_from=valid_from,
            valid_to=valid_to
        )
        coupon.save()
        messages.success(request, "Coupon added successfully.")
        return redirect('coupon_list')

    return render(request, 'admin/add_coupon.html')


@login_required
def edit_coupons(request, coupon_id):
    try:
        coupon = Coupons.objects.get(pk=coupon_id)
    except Coupons.DoesNotExist:
        return redirect('admin_coupons')

    if request.method == 'POST':
        coupon_code = request.POST.get('coupon_code')
        description = request.POST.get('description')
        minimum_amount = request.POST.get('minimum_amount')
        discount = request.POST.get('discount')
        valid_from = request.POST.get('valid_from')
        valid_to = request.POST.get('valid_to')

        # Check for empty fields
        if not (coupon_code and description and minimum_amount and discount and valid_from and valid_to):
            messages.error(request, "All fields are required.")
            return redirect('edit_coupons', coupon_id=coupon_id)

        try:
            minimum_amount = int(minimum_amount)
            discount = int(discount)
        except ValueError:
            messages.error(request, "Minimum Amount and Discount must be integers.")
            return redirect('edit_coupons', coupon_id=coupon_id)

        # Check if discount is greater than minimum amount
        if discount > minimum_amount:
            messages.error(request, "Discount cannot be greater than Minimum Amount.")
            return redirect('edit_coupons', coupon_id=coupon_id)

        if valid_from > valid_to:
            messages.error(request, "Valid From date should not be greater than Valid To date.")
            return redirect('edit_coupons', coupon_id=coupon_id)

        coupon.coupon_code = coupon_code
        coupon.description = description
        coupon.minimum_amount = minimum_amount
        coupon.discount = discount
        coupon.valid_from = valid_from
        coupon.valid_to = valid_to

        coupon.save()

        return redirect('coupon_list')

    context = {'coupon': coupon}
    return render(request, 'admin/edit_coupon.html', context)


def list_coupon(request, c_id):
    coupon = Coupons.objects.get(id=c_id)
    coupon.un_list = False
    coupon.save()
    return redirect('coupon_list')


def unlist_coupon(request, c_id):
    coupon = Coupons.objects.get(id=c_id)
    coupon.un_list = True
    coupon.save()
    return redirect('coupon_list')


def coupon_details(request, coupon_id):
    coupon = get_object_or_404(Coupons, id=coupon_id)
    used_users = UserCoupons.objects.filter(coupon=coupon)
    is_expired = coupon.valid_to < timezone.now()
    context = {
        'coupon': coupon,
        'used_users': used_users,
        'is_expired': is_expired,
    }

    return render(request, 'admin/coupon_details.html', context)


def offer_list(request):
    search_query = request.GET.get('search')
    offers = Offers.objects.all()
    if search_query:
        offers = offers.filter(Q(name__icontains=search_query))

    context = {
        'offers': offers,
    }
    return render(request, 'admin/offer_list.html', context)


def add_offers(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        discount_on = request.POST.get('discount_on')
        discount_type = request.POST.get('discount_type')
        discount_value = request.POST.get('discount_value')
        valid_from_str = request.POST.get('valid_from')
        valid_to_str = request.POST.get('valid_to')

        if not all([name, discount_on, discount_type, discount_value, valid_from_str, valid_to_str]):
            messages.error(request, 'All fields are required')
            return redirect('add_offers')
        try:
            valid_from = datetime.strptime(valid_from_str, '%Y-%m-%dT%H:%M')
            valid_to = datetime.strptime(valid_to_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            messages.error(request, 'Invalid date/time format')
            return redirect('add_offers')
        if valid_from >= valid_to:
            messages.error(request, 'Valid from date/time must be earlier than valid to date/time')
            return redirect('add_offers')

        if discount_type == 'percentage':
            try:
                discount_value = float(discount_value)

                if discount_value < 0 or discount_value > 100:
                    messages.error(request, 'Percentage value should be between 0 and 100')
                    return redirect('add_offers')
            except ValueError:
                messages.error(request, 'Invalid discount value for percentage')
                return redirect('add_offers')

        if discount_on == 'product':
            product_id = request.POST.get('product')
            try:
                product = Products.objects.get(id=product_id)
                category = None
            except Products.DoesNotExist:
                messages.error(request, 'Invalid product ID')
                return redirect('add_offers')
        else:
            category_id = request.POST.get('category')
            try:
                category = Category.objects.get(id=category_id)
                product = None
            except Category.DoesNotExist:
                messages.error(request, 'Invalid category ID')
                return redirect('add_offers')

        offer = Offers(
            name=name,
            discount_on=discount_on,
            discount_type=discount_type,
            product=product,
            category=category,
            discount_value=discount_value,
            valid_to=valid_to,
            valid_from=valid_from
        )
        offer.save()
        return redirect('offer_list')

    products = Products.objects.all()
    categories = Category.objects.all()
    context = {
        'products': products,
        'categories': categories,
    }
    return render(request, 'admin/add_offer.html', context)


def unlist(request, o_id):
    offer = Offers.objects.get(id=o_id)
    offer.is_unlisted = True
    offer.save()
    return redirect('offer_list')


def List(request, o_id):
    offer = Offers.objects.get(id=o_id)
    offer.is_unlisted = False
    offer.save()
    return redirect('offer_list')


def edit_offers(request, o_id):
    offer = get_object_or_404(Offers, id=o_id)
    products = Products.objects.all()
    categories = Category.objects.all()

    if request.method == 'POST':
        name = request.POST.get('name')
        discount_on = request.POST.get('discount_on')
        discount_type = request.POST.get('discount_type')
        discount_value = request.POST.get('discount_value')
        valid_from_str = request.POST.get('valid_from')
        valid_to_str = request.POST.get('valid_to')

        # Check for empty fields
        if not all([name, discount_on, discount_type, discount_value, valid_from_str, valid_to_str]):
            messages.error(request, 'All fields are required')
            return redirect('edit_offers', o_id=o_id)

        # Convert string datetime to datetime objects
        try:
            valid_from = datetime.strptime(valid_from_str, '%Y-%m-%dT%H:%M')
            valid_to = datetime.strptime(valid_to_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            messages.error(request, 'Invalid date/time format')
            return redirect('edit_offers', o_id=o_id)

        # Check if valid_from is greater than valid_to
        if valid_from >= valid_to:
            messages.error(request, 'Valid from date/time must be earlier than valid to date/time')
            return redirect('edit_offers', o_id=o_id)

        if discount_type == 'percentage':
            # Validate discount value for percentage type
            try:
                discount_value = float(discount_value)
                if discount_value < 0 or discount_value > 100:
                    messages.error(request, 'Percentage value should be between 0 and 100')
                    return redirect('edit_offers', o_id=o_id)
            except ValueError:
                messages.error(request, 'Invalid discount value for percentage')
                return redirect('edit_offers', o_id=o_id)

        if discount_on == 'product':
            product_id = request.POST.get('product')
            try:
                product = Products.objects.get(id=product_id)
            except Products.DoesNotExist:
                messages.error(request, 'Invalid product ID')
                return redirect('edit_offers', o_id=o_id)
            category = None
        else:
            category_id = request.POST.get('category')
            try:
                category = Category.objects.get(id=category_id)
            except Category.DoesNotExist:
                messages.error(request, 'Invalid category ID')
                return redirect('edit_offers', o_id=o_id)
            product = None

        # Update the offer fields and save
        offer.name = name
        offer.discount_on = discount_on
        offer.discount_type = discount_type
        offer.product = product
        offer.category = category
        offer.discount_value = discount_value
        offer.valid_to = valid_to
        offer.valid_from = valid_from
        offer.save()

        return redirect('offer_list')

    context = {
        'offer': offer,
        'products': products,
        'categories': categories,
    }
    return render(request, 'admin/edit_offer.html', context)


# def add_variants(request, p_id):
#     product = get_object_or_404(Products, id=p_id)
#     variants = ProductAttribute.objects.filter(product=product)
#     choices= ProductAttribute.SIZE_CHOICES
#
#     if request.method == 'POST':
#         size = request.POST.get('size')
#         quantity = request.POST.get('quantity')
#
#         if not size or not quantity:
#             messages.error(request, "Size and Quantity are required")
#             return redirect('add_variants', p_id=p_id)
#
#         try:
#             quantity = int(quantity)
#             if quantity < 0:
#                 messages.error(request, "Quantity should not be negative")
#                 return redirect('add_variants', p_id=p_id)
#         except ValueError:
#             messages.error(request, "Invalid quantity")
#             return redirect('add_variants', p_id=p_id)
#
#         attribute = ProductAttribute(product=product, size=size, quantity=quantity)
#         attribute.save()
#         return redirect('add_variants', p_id=p_id)
#
#     context = {
#         'variants': variants,
#         'product': product,
#         'choices': choices,
#     }
#     return render(request, 'admin/add_variants.html', context)




def add_variants(request, p_id):
    product = get_object_or_404(Products, id=p_id)
    variants = ProductAttribute.objects.filter(product=product)
    choices = ProductAttribute.SIZE_CHOICES

    if request.method == 'POST':
        size = request.POST.get('size')
        quantity = request.POST.get('quantity')

        if not size or not quantity:
            messages.error(request, "Size and Quantity are required")
            return redirect('add_variants', p_id=p_id)

        try:
            size_int = int(size)  # Convert 'size' to an integer
            quantity_int = int(quantity)

            if quantity_int < 0:
                messages.error(request, "Quantity should not be negative")
                return redirect('add_variants', p_id=p_id)

            attribute = ProductAttribute(product=product, size=size_int, quantity=quantity_int)
            attribute.save()
            return redirect('add_variants', p_id=p_id)

        except ValueError:
            messages.error(request, "Invalid size or quantity")
            return redirect('add_variants', p_id=p_id)

    context = {
        'variants': variants,
        'product': product,
        'choices': choices,
    }
    return render(request, 'admin/add_variants.html', context)


def unlist_variants(request, p_id, v_id):
    variant = get_object_or_404(ProductAttribute, id=v_id)
    variant.unlist = True
    variant.save()
    return redirect('add_variants', p_id=p_id)


def list_variants(request, p_id, v_id):
    variant = get_object_or_404(ProductAttribute, id=v_id)
    variant.unlist = False
    variant.save()
    return redirect('add_variants', p_id=p_id)


def edit_variants(request,p_id,v_id):
    product = get_object_or_404(Products, id=p_id)
    variant_list = ProductAttribute.objects.filter(product=product)
    variant = ProductAttribute.objects.get(product=product,id=v_id)
    choices = ProductAttribute.SIZE_CHOICES


    if request.method=='POST':
        size = request.POST.get('size')
        quantity = request.POST.get('quantity')

        if not size or not quantity:
            messages.error(request, "Size and Quantity are required")
            return redirect('edit_variants', p_id=p_id,v_id=v_id)

        try:
            quantity = int(quantity)
            if quantity < 0:
                messages.error(request, "Quantity should not be negative")
                return redirect('edit_variants', p_id=p_id,v_id=v_id)
        except ValueError:
            messages.error(request, "Invalid quantity")
            return redirect('edit_variants', p_id=p_id,v_id=v_id)

        variant.size=size
        variant.quantity=quantity
        variant.save()
        return redirect('add_variants', p_id=p_id)

    context={
        'variants': variant_list,
        'variant': variant,
        'product': product,
        'choices': choices,
        'selected_size':variant.size,
    }
    return render(request,'admin/edit_variants.html',context)



