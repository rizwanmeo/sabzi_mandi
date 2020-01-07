from dukan.models import Shop

def default_shop(request):
    """ 
    Adds Player to context
    """
    context = {}
    shop_id = request.GET.get('shop_id', 0)
    if request.user.is_authenticated:
        if shop_id == 0:
            shop_qs = request.user.shop_set.all()
            if shop_qs.count() > 0:
                try:
                    context['shop'] = shop_qs.get(is_default=True)
                except:
                    context['shop'] = shop_qs[0]
        else:
            context['shop'] = request.user.shop_set.get(id=int(shop_id))
    return context
