from django.views.generic import ListView, DetailView
from geocontext.models.collection import Collection


class CollectionListView(ListView):
    """List view for Context Collection."""

    model = Collection
    template_name = 'geocontext/collection_list.html'
    object_name = 'collection_list'
    paginate_by = 10


class CollectionDetailView(DetailView):
    """Detail view for Context Collection."""

    model = Collection
    template_name = 'geocontext/collection_detail.html'
    object_name = 'collection'
    slug_field = 'key'
