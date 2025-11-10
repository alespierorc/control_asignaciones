from django import forms
from django.contrib.auth.models import User
from .models import Expediente, OficinaRegional, Contrato

# ---------- Programar fecha (si lo usas en otra vista) ----------
class ProgramarVisitaForm(forms.ModelForm):
    class Meta:
        model = Expediente
        fields = ["fecha_visita"]
        widgets = {
            "fecha_visita": forms.DateInput(attrs={"type": "date", "class": "i-date"})
        }
    def clean_fecha_visita(self):
        fv = self.cleaned_data.get("fecha_visita")
        if not fv:
            raise forms.ValidationError("Debes seleccionar una fecha de visita.")
        return fv

# ---------- CONCLUIR (requerido por tus vistas) ----------
class ConcluirForm(forms.ModelForm):
    class Meta:
        model = Expediente
        fields = ["fecha_derivacion", "observaciones"]
        widgets = {
            "fecha_derivacion": forms.DateInput(attrs={"type": "date", "class": "i-date"}),
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

# ---------- Registrar datos de visita (Supervisor) ----------
class SupervisorVisitaForm(forms.Form):
    siged = forms.ChoiceField(
        label="N.º SIGED", choices=[], required=False,
        widget=forms.Select(attrs={"class": "i-select"})
    )
    codigo = forms.CharField(
        label="Código", required=False,
        widget=forms.TextInput(attrs={"readonly": "readonly", "class": "i-ro"})
    )
    tipo_supervision = forms.CharField(
        label="Tipo de supervisión", required=False,
        widget=forms.TextInput(attrs={"readonly": "readonly", "class": "i-ro"})
    )
    estado = forms.CharField(
        label="Estado del expediente", required=False,
        widget=forms.TextInput(attrs={"readonly": "readonly", "class": "i-ro"})
    )
    visita_decision = forms.CharField(required=False, widget=forms.HiddenInput())
    fecha_visita = forms.DateField(
        required=False, widget=forms.DateInput(attrs={"type": "date", "class": "i-date"})
    )

    def set_siged_choices(self, expedientes):
        opciones = [("", "— Selecciona un expediente —")]
        for e in expedientes:
            label = f"{e.siged} — {e.codigo or 's/código'}"
            opciones.append((e.siged, label))
        self.fields["siged"].choices = opciones

# ---------- Registro del Coordinador ----------
class CoordinadorRegistroForm(forms.ModelForm):
    class Meta:
        model = Expediente
        fields = [
            "siged", "codigo", "oficina", "contrato", "supervisor",
            "tipo_supervision", "tipo_documento", "carta_linea",
        ]
        widgets = {
            "siged": forms.TextInput(attrs={"placeholder": "N.º SIGED"}),
            "codigo": forms.TextInput(attrs={"placeholder": "Código"}),
            "oficina": forms.Select(attrs={"class": "i-select"}),
            "contrato": forms.Select(attrs={"class": "i-select"}),
            "supervisor": forms.Select(attrs={"class": "i-select"}),
            "tipo_supervision": forms.Select(attrs={"class": "i-select"}),
            "tipo_documento": forms.Select(attrs={"class": "i-select"}),
            "carta_linea": forms.TextInput(attrs={"placeholder": "Opcional"}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["supervisor"].queryset = User.objects.all().order_by("username")
        self.fields["oficina"].queryset = OficinaRegional.objects.all().order_by("nombre")
        self.fields["contrato"].queryset = Contrato.objects.all().order_by("numero")
