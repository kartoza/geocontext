from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns

from geocontext.api_views.cache import CacheValueListAPI
from geocontext.api_views.collection import CollectionValueAPIView
from geocontext.api_views.csr import CSRListAPIView, CSRDetailAPIView, get_context
from geocontext.api_views.group import GroupValueAPIView
from geocontext.api_views.river import RiverNameAPIView
from geocontext.views.csr import CSRListView, CSRDetailView
from geocontext.views.group import GroupListView, GroupDetailView
from geocontext.views.collection import CollectionListView, CollectionDetailView


urlpatterns = [
    url(regex=r'^geocontext/$',
        view=get_context,
        name='geocontext-retrieve'),
    url(regex=r'^geocontext/csr/list/$',
        view=CSRListView.as_view(),
        name='csr-list'),
    url(regex=r'^geocontext/csr/(?P<slug>[\w-]+)/$',
        view=CSRDetailView.as_view(),
        name='csr-detail'),
    url(regex=r'^geocontext/group/list/$',
        view=GroupListView.as_view(),
        name='group-list'),
    url(regex=r'^geocontext/group/(?P<slug>[\w-]+)/$',
        view=GroupDetailView.as_view(),
        name='group-detail'),
    url(regex=r'^geocontext/collection/list/$',
        view=CollectionListView.as_view(),
        name='collection-list'),
    url(regex=r'^geocontext/collection/(?P<slug>[\w-]+)/$',
        view=CollectionDetailView.as_view(),
        name='collection-detail'),
]

urlpatterns_api = [
    url(regex=r'^geocontext/csr/$',
        view=CSRListAPIView.as_view(),
        name='service-registry-list-api'
        ),
    url(regex=r'^geocontext/csr/(?P<key>[\w-]+)/$',
        view=CSRDetailAPIView.as_view(),
        name='service-registry-detail-api'
        ),
    url(regex=r'^geocontext/value/list/'
              r'(?P<x>[+-]?[0-9]+[.]?[0-9]*)/'
              r'(?P<y>[+-]?[0-9]+[.]?[0-9]*)/'
              r'(?P<csr_keys>[\w\-,]+)/$',
        view=CacheValueListAPI.as_view(),
        name='value-list-csr-api'
        ),
    url(regex=r'^geocontext/value/collection/'
              r'(?P<x>[+-]?[0-9]+[.]?[0-9]*)/'
              r'(?P<y>[+-]?[0-9]+[.]?[0-9]*)/'
              r'(?P<collection_key>[\w\-,]+)/$',
        view=CollectionValueAPIView.as_view(),
        name='collection-list-api'
        ),
    url(regex=r'^geocontext/value/group/'
              r'(?P<x>[+-]?[0-9]+[.]?[0-9]*)/'
              r'(?P<y>[+-]?[0-9]+[.]?[0-9]*)/'
              r'(?P<group_key>[\w\-,]+)/$',
        view=GroupValueAPIView.as_view(),
        name='group-list-api'
        ),
    url(regex=r'^geocontext/river-name/'
              r'(?P<x>[+-]?[0-9]+[.]?[0-9]*)/'
              r'(?P<y>[+-]?[0-9]+[.]?[0-9]*)/$',
        view=RiverNameAPIView.as_view(),
        name='river-name-api'
        ),
]

urlpatterns_api = format_suffix_patterns(urlpatterns_api)
