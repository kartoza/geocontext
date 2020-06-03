from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns

from geocontext.api_views.cache import CacheListAPI
from geocontext.api_views.collection import CollectionAPIView
from geocontext.api_views.csr import CSRListAPIView, CSRDetailAPIView, get_csr
from geocontext.api_views.group import GroupAPIView
from geocontext.api_views.river import RiverNameAPIView
from geocontext.views.collection import CollectionListView, CollectionDetailView
from geocontext.views.csr import CSRListView, CSRDetailView
from geocontext.views.group import GroupListView, GroupDetailView


urlpatterns = [
    url(regex=r'^geocontext/$',
        view=get_csr,
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

# We allow +-DD.DDD OR degree:minute:second:direction format & Optional SRID
urlpatterns_api = [
    url(regex=r'^geocontext/csr/$',
        view=CSRListAPIView.as_view(),
        name='service-registry-list-api'
        ),
    url(regex=r'^geocontext/csr/(?P<key>[\w-]+)/$',
        view=CSRDetailAPIView.as_view(),
        name='service-registry-detail-api'
        ),
    url(regex=r'^geocontext/value/cache/'
              r'(?P<x>(-?[0-9]{1,3}(?:\.[0-9]{1,10})?)|(\d{1,3}(:[0-5][1-9]){2}\.?(\d{1,6})?:[EW](?i)))/'  # noqa
              r'(?P<y>(-?[0-9]{1,3}(?:\.[0-9]{1,10})?)|(\d{1,3}(:[0-5][1-9]){2}\.?(\d{1,6})?:[NS](?i)))/'  # noqa
              r'((?P<srid>[0-9]+)/)?$',
        view=CacheListAPI.as_view(),
        name='cache-list-csr-api'
        ),
    url(regex=r'^geocontext/value/collection/'
              r'(?P<x>(-?[0-9]{1,3}(?:\.[0-9]{1,10})?)|(\d{1,3}(:[0-5][1-9]){2}\.?(\d{1,6})?:[EW](?i)))/'  # noqa
              r'(?P<y>(-?[0-9]{1,3}(?:\.[0-9]{1,10})?)|(\d{1,3}(:[0-5][1-9]){2}\.?(\d{1,6})?:[NS](?i)))/'  # noqa
              r'(?P<collection_key>[\w\-,]+)/'
              r'((?P<srid>[0-9]+)/)?$',
        view=CollectionAPIView.as_view(),
        name='collection-list-api'
        ),
    url(regex=r'^geocontext/value/group/'
              r'(?P<x>(-?[0-9]{1,3}(?:\.[0-9]{1,10})?)|(\d{1,3}(:[0-5][0-9]){2}\.?(\d{1,6})?:[EW](?i)))/'  # noqa
              r'(?P<y>(-?[0-9]{1,3}(?:\.[0-9]{1,10})?)|(\d{1,3}(:[0-5][0-9]){2}\.?(\d{1,6})?:[NS](?i)))/'  # noqa
              r'(?P<group_key>[\w\-,]+)/'
              r'((?P<srid>[0-9]+)/)?$',
        view=GroupAPIView.as_view(),
        name='group-list-api'
        ),
    url(regex=r'^geocontext/river-name/'
              r'(?P<x>(-?[0-9]{1,3}(?:\.[0-9]{1,10})?)|(\d{1,3}(:[0-5][1-9]){2}\.?(\d{1,6})?:[EW](?i)))/'  # noqa
              r'(?P<y>(-?[0-9]{1,3}(?:\.[0-9]{1,10})?)|(\d{1,3}(:[0-5][1-9]){2}\.?(\d{1,6})?:[NS](?i)))/$',  # noqa
        view=RiverNameAPIView.as_view(),
        name='river-name-api'
        ),
]

urlpatterns_api = format_suffix_patterns(urlpatterns_api)
