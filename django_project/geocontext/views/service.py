from geocontext.models.service import Service
from django.views.generic import DetailView, ListView


class ServiceListView(ListView):
    """List view for Service."""

    model = Service
    template_name = 'geocontext/service_list.html'
    object_name = 'service_list'
    paginate_by = 10


class ServiceDetailView(DetailView):
    """Detail view for Service."""

    model = Service
    template_name = 'geocontext/service_detail.html'
    object_name = 'service'
    slug_field = 'key'
