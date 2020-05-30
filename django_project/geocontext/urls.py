from django.conf.urls import url

from rest_framework.urlpatterns import format_suffix_patterns

from geocontext.views.api import (
    ContextServiceRegistryListAPIView,
    ContextServiceRegistryDetailAPIView,
    ContextValueGeometryListAPI,
    ContextGroupValueAPIView,
    ContextCollectionValueAPIView,
    RiverNameAPIView,
    get_context
)

from geocontext.views.context_service_registry import (
    ContextServiceRegistryListView,
    ContextServiceRegistryDetailView,
)
from geocontext.views.context_group import (
    ContextGroupListView, ContextGroupDetailView)
from geocontext.views.context_collection import (
    ContextCollectionListView, ContextCollectionDetailView)


urlpatterns = [
    url(regex=r'^geocontext/$',
        view=get_context,
        name='geocontext-retrieve'),
    # Context Service Registry
    url(regex=r'^geocontext/csr/list/$',
        view=ContextServiceRegistryListView.as_view(),
        name='csr-list'),
    url(regex=r'^geocontext/csr/(?P<slug>[\w-]+)/$',
        view=ContextServiceRegistryDetailView.as_view(),
        name='csr-detail'),
    # Context Group
    url(regex=r'^geocontext/context-group/list/$',
        view=ContextGroupListView.as_view(),
        name='context-group-list'),
    url(regex=r'^geocontext/context-group/(?P<slug>[\w-]+)/$',
        view=ContextGroupDetailView.as_view(),
        name='context-group-detail'),
    # Context Collection
    url(regex=r'^geocontext/context-collection/list/$',
        view=ContextCollectionListView.as_view(),
        name='context-collection-list'),
    url(regex=r'^geocontext/context-collection/(?P<slug>[\w-]+)/$',
        view=ContextCollectionDetailView.as_view(),
        name='context-collection-detail'),
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
    # url(regex=r'^geocontext/value/list/'
    #           r'(?P<x>[+-]?[0-9]+[.]?[0-9]*)/'
    #           r'(?P<y>[+-]?[0-9]+[.]?[0-9]*)/$',
    #     view=ContextValueGeometryListAPI.as_view(),
    #     name='context-value-list-all-api'
    #     ),
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
    # Get river name
    url(regex=r'^geocontext/river-name/'
              r'(?P<x>[+-]?[0-9]+[.]?[0-9]*)/'
              r'(?P<y>[+-]?[0-9]+[.]?[0-9]*)/$',
        view=RiverNameAPIView.as_view(),
        name='river-name-api'
        ),
]

urlpatterns_api = format_suffix_patterns(urlpatterns_api)
