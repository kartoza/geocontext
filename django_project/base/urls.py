from django.urls import path
from django.views.generic import TemplateView
from django.conf.urls import url, include

from rest_framework.documentation import include_docs_urls
from geocontext.urls import urlpatterns as geocontext_urls
from geocontext.urls import urlpatterns_api_v1
from geocontext.urls import urlpatterns_api_v2


urlpatterns = [
    path('', TemplateView.as_view(template_name='landing_page.html')),
    url('^getting_started/', TemplateView.as_view(template_name='getting_started.html')),
    url('^map_view/', TemplateView.as_view(template_name='map_view.html')),
    url('^signup/', TemplateView.as_view(template_name='signup.html')),
    url('^api/v1/', include(urlpatterns_api_v1)),
    url('^api/v2/', include(urlpatterns_api_v2)),
    url('', include(geocontext_urls)),
    url(r'^docs/', include_docs_urls(title='GeoContext API'))
]
