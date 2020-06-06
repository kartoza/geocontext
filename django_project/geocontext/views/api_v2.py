from rest_framework import views


class QueryView(views.APIView):
    def get(self, request):
        print(request)
