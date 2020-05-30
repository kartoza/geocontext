from django import forms
from geocontext.models.context_service_registry import ContextServiceRegistry


def get_context_service_registry():
    service_registry_choices = [
        (m.key, m.name) for m in ContextServiceRegistry.objects.all()]
    return service_registry_choices


class GeoContextForm(forms.Form):
    x = forms.FloatField(label='X Coordinate', required=True)
    y = forms.FloatField(label='Y Coordinate', required=True)
    srid = forms.IntegerField(label='SRID')
    service_registry_key = forms.ChoiceField(
        label='Service Registry key',
        required=True,
        choices=get_context_service_registry
    )
