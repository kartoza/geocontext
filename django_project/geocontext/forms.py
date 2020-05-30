from django import forms
from geocontext.models.csr import ContextServiceRegistry


def get_csr():
    service_registry_choices = [
        (m.key, m.name) for m in ContextServiceRegistry.objects.all()]
    return service_registry_choices


class GeoContextForm(forms.Form):
    x = forms.CharField(label='X Coordinate', required=True)
    y = forms.CharField(label='Y Coordinate', required=True)
    srid = forms.IntegerField(label='SRID')
    service_registry_key = forms.ChoiceField(
        label='Service Registry key',
        required=True,
        choices=get_csr
    )
