from django.utils.deprecation import MiddlewareMixin

class SabziMandiMiddleware(MiddlewareMixin):

    def process_request(self, request):
        shop_id = request.GET.get('shop_id', 0)
        request.shop = None
        if request.user.is_authenticated:
            if shop_id == 0:
                shop_qs = request.user.shop_set.all()
                if shop_qs.count() > 0:
                    try:
                        request.shop = shop_qs.get(is_default=True)
                    except:
                        request.shop = shop_qs[0]
            else:
                if bool(shop_id):
                    request.shop = request.user.shop_set.get(id=shop_id)
                else:
                    request.shop = None

        return None

    def process_response(self, request, response):
        return response
