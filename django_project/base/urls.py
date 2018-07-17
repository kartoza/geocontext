# coding=utf-8

from django.urls import path
from django.views.generic import TemplateView
from django.conf.urls import url, include

from geocontext.urls import urlpatterns as geocontext_urls
from geocontext.urls import urlpatterns_api as geocontext_url_api


urlpatterns = [
    path('', TemplateView.as_view(template_name="landing_page.html")),
    url('^api/v1/', include(geocontext_url_api)),
    url('', include(geocontext_urls))
]
