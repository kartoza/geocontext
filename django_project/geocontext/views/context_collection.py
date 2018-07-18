# coding=utf-8
"""View for Context Collection."""

from django.views.generic import ListView
from geocontext.models.context_collection import ContextCollection


class ContextCollectionListView(ListView):
    """List view for Context Collection."""

    model = ContextCollection
    template_name = 'geocontext/context_collection_list.html'
    context_object_name = 'context_collection_list'
    paginate_by = 10
