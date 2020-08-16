from json import dumps
from geocontext.models.service import Service
from geocontext.models.group import Group
from geocontext.models.collection import Collection


def add_variable_to_context(request):
    context = {
        'services': dumps(list(Service.objects.all().values('key', 'name'))),
        'groups': dumps(list(Group.objects.all().values('key', 'name'))),
        'collections': dumps(list(Collection.objects.all().values('key', 'name')))
    }
    return context
