# coding=utf-8
"""URLs for GeoContext app."""

from django.conf.urls import url

from rest_framework.urlpatterns import format_suffix_patterns

from geocontext.views import (
    get_context,
    ContextServiceRegistryList,
    ContextServiceRegistryDetail
)

urlpatterns = [
    url(regex=r'^geocontext/$',
        view=get_context,
        name='geocontext-retrieve'),
]

urlpatterns_api = [
    url(regex=r'^geocontext/csr/$',
        view=ContextServiceRegistryList.as_view(),
        name='context-service-registry-list'
        ),
    url(regex=r'^geocontext/csr/(?P<key>[\w-]+)/$',
        view=ContextServiceRegistryDetail.as_view(),
        name='context-service-registry-detail'
        ),
]

urlpatterns_api = format_suffix_patterns(urlpatterns_api)

urlpatterns += urlpatterns_api
