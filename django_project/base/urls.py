from rest_framework.authtoken.views import obtain_auth_token

from django.urls import path
from django.views.generic import TemplateView
from django.conf.urls import url, include

from geocontext.urls import urlpatterns as geocontext_urls
from geocontext.urls import urlpatterns_api_v1
from geocontext.urls import urlpatterns_api_v2


urlpatterns = [
    path('', TemplateView.as_view(template_name='landing_page.html')),
    path('api-token-auth/', obtain_auth_token, name='api_token_auth'),
    url('^getting_started/', TemplateView.as_view(template_name='getting_started.html')),
    url('^map_view/', TemplateView.as_view(template_name='map_view.html')),
    url('^signup/', TemplateView.as_view(template_name='signup.html')),
    url('^api/v1/', include(urlpatterns_api_v1)),
    url('^api/v2/', include(urlpatterns_api_v2)),
    url('', include(geocontext_urls)),
]
