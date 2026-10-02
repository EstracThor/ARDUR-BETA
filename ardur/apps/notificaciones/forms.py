from django import forms
from django.contrib.auth import get_user_model
from ardur.apps.expedientes.models import Expediente

class LoteForm(forms.Form):
    fecha_programada = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label='Fecha programada')
    notificador = forms.ModelChoiceField(queryset=get_user_model().objects.none(), label='Notificador')
    expedientes = forms.ModelMultipleChoiceField(queryset=Expediente.objects.none(), widget=forms.CheckboxSelectMultiple)
    def __init__(self, *args, orden, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['notificador'].queryset = get_user_model().objects.filter(is_active=True, groups__name='NOTIFICADOR').distinct()
        self.fields['expedientes'].queryset = Expediente.objects.filter(orden=orden, estado='LISTO_PARA_NOTIFICAR', asignacion__isnull=True)

class ResultadoForm(forms.Form):
    estado = forms.ChoiceField(choices=[('ENTREGADO', 'Entregado'), ('NO_LOCALIZADO', 'No localizado'), ('INCIDENCIA', 'Incidencia')])
    observaciones = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3}))
