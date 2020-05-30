from django.views.generic import ListView, DetailView
from geocontext.models.group import ContextGroup


class GroupListView(ListView):
    """List view for Context Group."""

    model = ContextGroup
    template_name = 'geocontext/group_list.html'
    object_name = 'group_list'
    paginate_by = 10


class GroupDetailView(DetailView):
    """Detail view for Context Group."""

    model = ContextGroup
    template_name = 'geocontext/group_detail.html'
    object_name = 'group'
    slug_field = 'key'
