from django import forms
from django.contrib.auth.models import User
from .models import Expediente, OficinaRegional, Contrato


# ============================================================
#               FORMULARIO DEL COORDINADOR
# ============================================================
class CoordinadorRegistroForm(forms.ModelForm):
    """
    Formulario para registrar un nuevo expediente.
    Incluye los 12 campos solicitados por orden.
    """

    VISITA_CHOICES = [
        ("SI", "Sí"),
        ("NO", "No"),
    ]

    # Campo adicional tipo checkbox con opción sí/no
    visita_decision = forms.ChoiceField(
        choices=VISITA_CHOICES,
        label="¿Visita programada?",
        widget=forms.Select(attrs={"class": "i-select"}),
        required=True,
    )

    # Fecha editable
    fecha_asignacion = forms.DateField(
        label="Fecha de asignación",
        widget=forms.DateInput(attrs={"type": "date", "class": "i-date"}),
        required=True,
    )

    class Meta:
        model = Expediente
        fields = [
            "contrato",           # 1
            "siged",              # 2
            "carta_linea",        # 3
            "codigo",             # 4 (Código OSINERGMIN)
            "codigo_actividad",   # 5
            "razon_social",       # 6
            "tipo_supervision",   # 7
            "tipo_documento",     # 8
            "oficina",            # 9
            "supervisor",         # 10
            "visita_decision",    # 11
            "fecha_asignacion",   # 12
        ]

        widgets = {
            "contrato": forms.Select(attrs={"class": "i-select"}),
            "siged": forms.TextInput(attrs={"placeholder": "Ej. 2025-XXXX"}),
            "carta_linea": forms.TextInput(attrs={"placeholder": "Ej. Carta N° 045-2025-OSINERGMIN"}),
            "codigo": forms.TextInput(attrs={"placeholder": "Ej. COD-1234"}),
            "codigo_actividad": forms.TextInput(attrs={"placeholder": "Ej. ACT-5678"}),
            "razon_social": forms.TextInput(attrs={"placeholder": "Ej. Nombre del agente o instalación"}),
            "tipo_supervision": forms.Select(attrs={"class": "i-select"}),
            "tipo_documento": forms.Select(attrs={"class": "i-select"}),
            "oficina": forms.Select(attrs={"class": "i-select"}),
            "supervisor": forms.Select(attrs={"class": "i-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ordenar selects y configurar queryset
        self.fields["supervisor"].queryset = User.objects.all().order_by("username")
        self.fields["oficina"].queryset = OficinaRegional.objects.all().order_by("nombre")
        self.fields["contrato"].queryset = Contrato.objects.all().order_by("numero")

        # Hacer algunos campos obligatorios visualmente
        self.fields["siged"].required = True
        self.fields["carta_linea"].required = True
        self.fields["razon_social"].required = True


# ============================================================
#               FORMULARIOS ADICIONALES (Supervisor)
# ============================================================
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


class ConcluirForm(forms.ModelForm):
    class Meta:
        model = Expediente
        fields = ["fecha_derivacion", "observaciones"]
        widgets = {
            "fecha_derivacion": forms.DateInput(attrs={"type": "date", "class": "i-date"}),
            "observaciones": forms.Textarea(attrs={"rows": 4, "placeholder": "Observaciones de la conclusión…"}),
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
# ---------- Registro del Supervisor ----------
class SupervisorVisitaForm(forms.ModelForm):
    """
    Formulario usado por el supervisor para registrar una visita:
    - Selecciona el N° SIGED asignado.
    - Indica si hay visita (Sí/No).
    - Registra la fecha de visita.
    """
    class Meta:
        model = Expediente
        fields = ["visita_decision", "fecha_visita"]
        widgets = {
            "visita_decision": forms.Select(
                choices=[("SI", "Sí"), ("NO", "No")],
                attrs={"class": "blue-select"},
            ),
            "fecha_visita": forms.DateInput(
                attrs={"type": "date", "class": "blue-input"},
            ),
        }

    def set_siged_choices(self, expedientes):
        """Permite poblar dinámicamente los expedientes disponibles en el select del template."""
        self.fields["siged_choices"] = forms.ChoiceField(
            choices=[(e.siged, e.siged) for e in expedientes],
            required=True,
            label="N° SIGED",
        )

class SupervisorEstadoForm(forms.ModelForm):
    class Meta:
        model = Expediente
        fields = ["fecha_derivacion", "concluido", "observaciones"]
        widgets = {
            "fecha_derivacion": forms.DateInput(
                attrs={"type": "date", "class": "blue-input"}
            ),
            "observaciones": forms.Textarea(
                attrs={
                    "rows": 6,
                    "class": "blue-textarea",
                    "placeholder": "Escribe observaciones (opcional)"
                }
            ),
        }