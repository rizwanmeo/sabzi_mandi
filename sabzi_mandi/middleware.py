from django.utils.deprecation import MiddlewareMixin

class SabziMandiMiddleware(MiddlewareMixin):

    def process_request(self, request):
        print("==============process_request================", request.method)
        print(dir(request))
        return None

    def process_response(self, request, response):
        print("==============process_response================")
        print(response)
        return response
