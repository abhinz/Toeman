from .models import Wishlist

def wishlist_count(request):
    wishlist_item_count = 0

    if request.user.is_authenticated:
        wishlist_item_count = Wishlist.objects.filter(user=request.user).count()

    return {'wishlist_item_count': wishlist_item_count}
