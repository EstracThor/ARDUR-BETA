from django import forms

class PreliminarForm(forms.Form):
    archivo_pdf = forms.FileField(label='PDF generado en Cabildo (opcional)', required=False)
    cantidad_titulos = forms.IntegerField(label='Cantidad de títulos (reportada)', min_value=0, required=False)
    recargo_reportado = forms.DecimalField(label='Recargo reportado por Cabildo', min_value=0, max_digits=18, decimal_places=2, required=False)
