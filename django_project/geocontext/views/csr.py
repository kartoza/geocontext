from django.views.generic import ListView, DetailView
from geocontext.models.csr import CSR


class CSRListView(ListView):
    """List view for CSR."""

    model = CSR
    template_name = 'geocontext/csr_list.html'
    object_name = 'csr_list'
    paginate_by = 10


class CSRDetailView(DetailView):
    """Detail view for CSR."""

    model = CSR
    template_name = 'geocontext/csr_detail.html'
    object_name = 'csr'
    slug_field = 'key'
