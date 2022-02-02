from django import forms
from geocontext.models.service import Service


def get_service():
    service_choices = [(m.key, m.name) for m in Service.objects.all()]
    return service_choices


class GeoContextForm(forms.Form):
    x = forms.CharField(label='X Coordinate', required=True)
    y = forms.CharField(label='Y Coordinate', required=True)
    srid = forms.IntegerField(label='SRID')
    service_key = forms.ChoiceField(
        label='Service key',
        required=True,
        choices=get_service
    )
