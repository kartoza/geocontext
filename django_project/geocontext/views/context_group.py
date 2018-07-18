# coding=utf-8
"""View for Context Group."""

from django.views.generic import ListView
from geocontext.models.context_group import ContextGroup


class ContextGroupListView(ListView):
    """List view for Context Group."""

    model = ContextGroup
    template_name = 'geocontext/context_group_list.html'
    context_object_name = 'context_group_list'
    paginate_by = 10
