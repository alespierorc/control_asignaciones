from django import forms
from .models import Expediente

class ProgramarVisitaForm(forms.ModelForm):
    class Meta:
        model = Expediente
        fields = ["fecha_visita"]
        widgets = {
            "fecha_visita": forms.DateInput(attrs={"type": "date"})
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
            "observaciones": forms.Textarea(attrs={"rows": 4, "placeholder": "Observaciones de la conclusión…"})
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
