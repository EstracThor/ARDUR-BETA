import re
from django import forms
from django.core.exceptions import ValidationError
from ardur.apps.catastro.models import Predio
from .models import RegistroCarteraStaging

class ImportacionForm(forms.Form):
    periodo = forms.CharField(label='Periodo (AAAA-MM)', max_length=7)
    hoja = forms.CharField(label='Hoja del Excel', initial='Sheet 1', max_length=255)
    archivo = forms.FileField(label='Cartera original (.xls / .xlsx)')
    def clean_periodo(self):
        value = self.cleaned_data['periodo']
        if not re.fullmatch(r'\d{4}-(0[1-9]|1[0-2])', value):
            raise ValidationError('Use AAAA-MM.')
        return value

class RevisionForm(forms.ModelForm):
    predio_id_manual = forms.UUIDField(label='ID de predio confirmado', required=False)
    decision = forms.ChoiceField(choices=[('ACEPTAR', 'Aceptar caso revisado'), ('EXCLUIR', 'Excluir de aprobación (conservar RAW)')])
    motivo = forms.CharField(label='Fundamento de la decisión', widget=forms.Textarea(attrs={'rows': 3}))
    class Meta:
        model = RegistroCarteraStaging
        fields = ['ciu', 'cedula_ruc', 'nombres', 'clave', 'suministro', 'direccion', 'parroquia', 'telefono', 'correo', 'total_emision', 'total_interes', 'total_coactiva', 'total_recargo', 'meses_deuda']
    def clean(self):
        data = super().clean()
        for key in ('total_emision', 'total_interes', 'total_coactiva', 'total_recargo'):
            if data.get(key) is not None and data[key] < 0:
                self.add_error(key, 'No se admite un valor negativo.')
        if data.get('decision') == 'ACEPTAR' and (not data.get('nombres') or not (data.get('clave') or data.get('ciu'))):
            raise ValidationError('Aceptar requiere nombre e identificador de caso.')
        return data
    def clean_predio_id_manual(self):
        value = self.cleaned_data.get('predio_id_manual')
        if value and not Predio.objects.filter(pk=value, version_id=self.instance.raw.importacion.catastro_version_id).exists():
            raise ValidationError('Predio inexistente en la versión de catastro de esta importación.')
        return value
