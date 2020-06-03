from django import forms
from geocontext.models.csr import CSR


def get_csr():
    csr_choices = [(m.key, m.name) for m in CSR.objects.all()]
    return csr_choices


class GeoContextForm(forms.Form):
    x = forms.CharField(label='X Coordinate', required=True)
    y = forms.CharField(label='Y Coordinate', required=True)
    srid = forms.IntegerField(label='SRID')
    service_registry_key = forms.ChoiceField(
        label='Service Registry key',
        required=True,
        choices=get_csr
    )
