# coding=utf-8
"""URLs for GeoContext app."""

from django.conf.urls import url

from rest_framework.urlpatterns import format_suffix_patterns

from geocontext.views import (
    get_context,
    ContextServiceRegistryList,
    ContextServiceRegistryDetail,
    ContextCacheList,
    CustomContextCacheList,
)

urlpatterns = [
    url(regex=r'^geocontext/$',
        view=get_context,
        name='geocontext-retrieve'),
]

urlpatterns_api = [
    # Context Service Registry
    url(regex=r'^geocontext/csr/$',
        view=ContextServiceRegistryList.as_view(),
        name='context-service-registry-list'
        ),
    url(regex=r'^geocontext/csr/(?P<key>[\w-]+)/$',
        view=ContextServiceRegistryDetail.as_view(),
        name='context-service-registry-detail'
        ),
    # Context Cache
    url(regex=r'^geocontext/cache/$',
        view=ContextCacheList.as_view(),
        name='context-cache-list'
        ),
    url(regex=r'^geocontext/cache/list/'
              r'(?P<x>[+-]?[0-9]+[.]?[0-9]*)/'
              r'(?P<y>[+-]?[0-9]+[.]?[0-9]*)/$',
        view=CustomContextCacheList.as_view(),
        name='context-cache-custom'
        ),
    url(regex=r'^geocontext/cache/list/'
              r'(?P<x>[+-]?[0-9]+[.]?[0-9]*)/'
              r'(?P<y>[+-]?[0-9]+[.]?[0-9]*)/'
              r'(?P<csr_keys>[\w\-,]+)/$',
        view=CustomContextCacheList.as_view(),
        name='context-cache-custom-csr'
        ),
]

urlpatterns_api = format_suffix_patterns(urlpatterns_api)

urlpatterns += urlpatterns_api
