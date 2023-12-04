def user_required(view_func):
    actual_decorator = user_passes_test(
        lambda u: u.is_active and not u.is_superuser,
        login_url='admin_home'  # Replace with the URL for admin home
    )
    return actual_decorator(view_func)


from django.contrib.auth.decorators import user_passes_test

def admin_required(view_func):
    actual_decorator = user_passes_test(
        lambda u: u.is_active and u.is_superuser,
        login_url='admin_login'
    )
    return actual_decorator(view_func)