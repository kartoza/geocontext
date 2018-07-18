# coding=utf-8
"""URLs for GeoContext app."""

from django.conf.urls import url

from rest_framework.urlpatterns import format_suffix_patterns

from geocontext.views.api import (
    ContextServiceRegistryListAPIView,
    ContextServiceRegistryDetailAPIView,
    ContextCacheListAPIView,
    ContextValueGeometryListAPI,
    ContextGroupValueAPIView,
    ContextCollectionValueAPIView,
    get_context
)

from geocontext.views.context_service_registry import (
    ContextServiceRegistryListView
)
from geocontext.views.context_group import ContextGroupListView
from geocontext.views.context_collection import ContextCollectionListView


urlpatterns = [
    url(regex=r'^geocontext/$',
        view=get_context,
        name='geocontext-retrieve'),
    url(regex=r'^geocontext/csr/list/$',
        view=ContextServiceRegistryListView.as_view(),
        name='csr-list'),
    url(regex=r'^geocontext/context-group/list/$',
        view=ContextGroupListView.as_view(),
        name='context-group-list'),
    url(regex=r'^geocontext/context-collection/list/$',
        view=ContextCollectionListView.as_view(),
        name='context-collection-list'),
]

urlpatterns_api = [
    # Context Service Registry
    url(regex=r'^geocontext/csr/$',
        view=ContextServiceRegistryListAPIView.as_view(),
        name='context-service-registry-list-api'
        ),
    url(regex=r'^geocontext/csr/(?P<key>[\w-]+)/$',
        view=ContextServiceRegistryDetailAPIView.as_view(),
        name='context-service-registry-detail-api'
        ),
    # Context Cache
    url(regex=r'^geocontext/cache/$',
        view=ContextCacheListAPIView.as_view(),
        name='context-cache-list-api'
        ),
    url(regex=r'^geocontext/value/list/'
              r'(?P<x>[+-]?[0-9]+[.]?[0-9]*)/'
              r'(?P<y>[+-]?[0-9]+[.]?[0-9]*)/$',
        view=ContextValueGeometryListAPI.as_view(),
        name='context-value-list-all-api'
        ),
    url(regex=r'^geocontext/value/list/'
              r'(?P<x>[+-]?[0-9]+[.]?[0-9]*)/'
              r'(?P<y>[+-]?[0-9]+[.]?[0-9]*)/'
              r'(?P<csr_keys>[\w\-,]+)/$',
        view=ContextValueGeometryListAPI.as_view(),
        name='context-value-list-csr-api'
        ),
    url(regex=r'^geocontext/value/collection/'
              r'(?P<x>[+-]?[0-9]+[.]?[0-9]*)/'
              r'(?P<y>[+-]?[0-9]+[.]?[0-9]*)/'
              r'(?P<context_collection_key>[\w\-,]+)/$',
        view=ContextCollectionValueAPIView.as_view(),
        name='context-collection-list-api'
        ),
    url(regex=r'^geocontext/value/group/'
              r'(?P<x>[+-]?[0-9]+[.]?[0-9]*)/'
              r'(?P<y>[+-]?[0-9]+[.]?[0-9]*)/'
              r'(?P<context_group_key>[\w\-,]+)/$',
        view=ContextGroupValueAPIView.as_view(),
        name='context-group-list-api'
        ),
]

urlpatterns_api = format_suffix_patterns(urlpatterns_api)
