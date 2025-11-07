# asignaciones/forms.py
from django import forms
from .models import Expediente

class ProgramarVisitaForm(forms.ModelForm):
    class Meta:
        model = Expediente
        fields = ["fecha_visita", "visita"]
        widgets = {
            "fecha_visita": forms.DateInput(attrs={"type": "date", "class": "date-in"}),
            "visita": forms.HiddenInput(),  # lo controlas con los botones Sí/No en la plantilla
        }

    def clean_fecha_visita(self):
        fv = self.cleaned_data.get("fecha_visita")
        if not fv:
            raise forms.ValidationError("Debes seleccionar una fecha de visita.")
        return fv


class ConcluirForm(forms.ModelForm):
    class Meta:
        model = Expediente
        fields = ["fecha_derivacion", "observaciones"]
        widgets = {
            "fecha_derivacion": forms.DateInput(attrs={"type": "date"}),
            "observaciones": forms.Textarea(
                attrs={"rows": 4, "placeholder": "Observaciones de la conclusión…"}
            ),
        }

    def __init__(self, *args, **kwargs):
        self._exp = kwargs.get("instance")
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        fd = cleaned.get("fecha_derivacion")
        if not fd:
            self.add_error("fecha_derivacion", "Debes indicar la fecha de derivación.")
        if fd and self._exp and self._exp.fecha_visita and fd < self._exp.fecha_visita:
            self.add_error("fecha_derivacion", "La fecha de derivación no puede ser anterior a la fecha de visita.")
        return cleaned


class CoordinadorRegistroForm(forms.ModelForm):
    class Meta:
        model = Expediente
        fields = [
            "siged",
            "oficina",
            "contrato",
            "supervisor",
            "tipo_supervision",
            "tipo_documento",
            "carta_linea",
        ]
        widgets = {
            "siged": forms.TextInput(attrs={"placeholder": "N.º SIGED", "class": "text-in"}),
            "oficina": forms.Select(attrs={"class": "select-in"}),
            "contrato": forms.Select(attrs={"class": "select-in"}),
            "supervisor": forms.Select(attrs={"class": "select-in"}),
            "tipo_supervision": forms.Select(attrs={"class": "select-in"}),
            "tipo_documento": forms.Select(attrs={"class": "select-in"}),
            "carta_linea": forms.TextInput(attrs={"placeholder": "Opcional", "class": "text-in"}),
        }
        help_texts = {"siged": "Ingresa el N.º SIGED único del expediente."}
