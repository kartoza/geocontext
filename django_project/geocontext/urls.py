from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns

from geocontext.views.api_v1 import (
    CacheListAPI,
    CollectionAPIView,
    get_service,
    GroupAPIView,
    ServiceDetailAPIView,
    ServiceListAPIView,
    RiverNameAPIView,
)
from geocontext.views.api_v2 import GenericAPIView
from geocontext.views.collection import CollectionListView, CollectionDetailView
from geocontext.views.pricing_plan import PricingPlanTemplateView
from geocontext.views.service import ServiceListView, ServiceDetailView
from geocontext.views.group import GroupListView, GroupDetailView


urlpatterns = [
    url(regex=r'^geocontext/$',
        view=get_service,
        name='geocontext-retrieve'),
    url(regex=r'^geocontext/service/list/$',
        view=ServiceListView.as_view(),
        name='service-list'),
    url(regex=r'^geocontext/service/(?P<slug>[\w-]+)/$',
        view=ServiceDetailView.as_view(),
        name='service-detail'),
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
    url(r'^pricing-plan/$',
        PricingPlanTemplateView.as_view(),
        name='collection-detail'),
]

urlpatterns_api_v1 = [
    url(regex=r'^geocontext/csr/$',
        view=ServiceListAPIView.as_view(),
        name='service-list-api'
        ),
    url(regex=r'^geocontext/csr/(?P<key>[\w-]+)/$',
        view=ServiceDetailAPIView.as_view(),
        name='service-detail-api'
        ),
    url(regex=r'^geocontext/value/list/'
              r'(?P<x>[+-]?[0-9]+[.]?[0-9]*)/'
              r'(?P<y>[+-]?[0-9]+[.]?[0-9]*)/$',
        view=CacheListAPI.as_view(),
        name='cache-list-api'
        ),
    url(regex=r'^geocontext/value/collection/'
              r'(?P<x>[+-]?[0-9]+[.]?[0-9]*)/'
              r'(?P<y>[+-]?[0-9]+[.]?[0-9]*)/'
              r'(?P<collection_key>[\w\-,]+)/$',
        view=CollectionAPIView.as_view(),
        name='collection-list-api'
        ),
    url(regex=r'^geocontext/value/group/'
              r'(?P<x>[+-]?[0-9]+[.]?[0-9]*)/'
              r'(?P<y>[+-]?[0-9]+[.]?[0-9]*)/'
              r'(?P<group_key>[\w\-,]+)/$',
        view=GroupAPIView.as_view(),
        name='group-list-api'
        ),
    url(regex=r'^geocontext/river-name/'
              r'(?P<x>[+-]?[0-9]+[.]?[0-9]*)/'
              r'(?P<y>[+-]?[0-9]+[.]?[0-9]*)/$',
        view=RiverNameAPIView.as_view(),
        name='river-name-api'
        ),
]

urlpatterns_api_v1 = format_suffix_patterns(urlpatterns_api_v1)

urlpatterns_api_v2 = [
    url(regex=r'^query$',
        view=GenericAPIView.as_view(),
        name='service-api'
        ),
]

urlpatterns_api_v2 = format_suffix_patterns(urlpatterns_api_v2)
