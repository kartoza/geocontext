from geocontext.models.service import Service
from geocontext.models.group import Group
from geocontext.models.collection import Collection


def add_variable_to_context(request):
    context = {
        'services': Service.objects.all().values('key', 'name'),
        'groups': Group.objects.all().values('key', 'name'),
        'collections': Collection.objects.all().values('key', 'name')
    }
    return context
