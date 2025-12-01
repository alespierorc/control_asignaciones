# ============================================================
#                      FORMS.PY - SERMINCO
# ============================================================
# Formularios oficiales del sistema corporativo SERMINCO
# Incluye: Coordinador, Supervisor, y Creación de Usuarios
# ============================================================

from django import forms
from django.contrib.auth.models import User, Group
from .models import (
    Expediente,
    OficinaRegional,
    Contrato,
    TipoSupervision,
    TipoDocumento,
)

# ============================================================
#               FORMULARIO DEL COORDINADOR
# ============================================================

class CoordinadorRegistroForm(forms.ModelForm):
    """
    Formulario para registrar un nuevo expediente.
    Incluye los campos requeridos por orden, conectados a las FK reales.
    """

    VISITA_CHOICES = [("SI", "Sí"), ("NO", "No")]

    visita_decision = forms.ChoiceField(
        choices=VISITA_CHOICES,
        label="¿Visita programada?",
        widget=forms.Select(attrs={"class": "i-select"}),
        required=True,
    )

    fecha_asignacion = forms.DateField(
        label="Fecha de asignación",
        widget=forms.DateInput(attrs={"type": "date", "class": "i-date"}),
        required=True,
    )

    class Meta:
        model = Expediente
        fields = [
            "contrato",
            "siged",
            "carta_linea",
            "codigo",
            "codigo_actividad",
            "razon_social",
            "tipo_supervision",
            "tipo_documento",
            "oficina",
            "supervisor",
            "visita_decision",
            "fecha_asignacion",
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

        # Filtramos valores según catálogos existentes
        self.fields["supervisor"].queryset = User.objects.filter(groups__name="Supervisor").order_by("username")
        self.fields["oficina"].queryset = OficinaRegional.objects.all().order_by("nombre")
        self.fields["contrato"].queryset = Contrato.objects.all().order_by("numero")
        self.fields["tipo_supervision"].queryset = TipoSupervision.objects.all().order_by("nombre")
        self.fields["tipo_documento"].queryset = TipoDocumento.objects.all().order_by("nombre")

        # Campos obligatorios
        self.fields["siged"].required = True
        self.fields["carta_linea"].required = True
        self.fields["razon_social"].required = True


# ============================================================
#               FORMULARIOS DEL SUPERVISOR
# ============================================================

class SupervisorVisitaForm(forms.ModelForm):
    """Formulario usado por el supervisor para registrar una visita."""

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
    """Formulario usado por el supervisor para marcar expedientes como concluidos."""

    class Meta:
        model = Expediente
        fields = ["fecha_derivacion", "observaciones"]
        widgets = {
            "fecha_derivacion": forms.DateInput(attrs={"type": "date", "class": "blue-input"}),
            "observaciones": forms.Textarea(
                attrs={"rows": 6, "class": "blue-textarea", "placeholder": "Escribe observaciones (opcional)"}
            ),
        }

    def clean_fecha_derivacion(self):
        fd = self.cleaned_data.get("fecha_derivacion")
        if not fd:
            raise forms.ValidationError("Debes indicar la fecha de derivación.")
        return fd


# ============================================================
#              FORMULARIOS AUXILIARES (VISITA Y CONCLUSIÓN)
# ============================================================

class ProgramarVisitaForm(forms.ModelForm):
    class Meta:
        model = Expediente
        fields = ["fecha_visita"]
        widgets = {"fecha_visita": forms.DateInput(attrs={"type": "date", "class": "i-date"})}


class ConcluirForm(forms.ModelForm):
    class Meta:
        model = Expediente
        fields = ["fecha_derivacion", "observaciones"]
        widgets = {
            "fecha_derivacion": forms.DateInput(attrs={"type": "date", "class": "i-date"}),
            "observaciones": forms.Textarea(attrs={"rows": 4, "placeholder": "Observaciones de la conclusión…"}),
        }

    def clean(self):
        cleaned = super().clean()
        fd = cleaned.get("fecha_derivacion")
        if not fd:
            self.add_error("fecha_derivacion", "Debes indicar la fecha de derivación.")
        return cleaned


# ============================================================
#             FORMULARIO: CREAR USUARIO + ASIGNAR ROL
# ============================================================

class CrearUsuarioForm(forms.ModelForm):
    """Formulario para crear usuarios y asignarles un grupo."""

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Contraseña", "class": "i-input"}),
        label="Contraseña"
    )
    confirmar_password = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Confirmar contraseña", "class": "i-input"}),
        label="Confirmar contraseña"
    )
    grupo = forms.ModelChoiceField(
        queryset=Group.objects.filter(name__in=["AdministradorLider", "Administrador", "Coordinador", "Supervisor"]),
        required=True,
        label="Rol del usuario",
        widget=forms.Select(attrs={"class": "i-select"})
    )

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email"]
        widgets = {
            "username": forms.TextInput(attrs={"class": "i-input", "placeholder": "Nombre de usuario"}),
            "first_name": forms.TextInput(attrs={"class": "i-input", "placeholder": "Nombre"}),
            "last_name": forms.TextInput(attrs={"class": "i-input", "placeholder": "Apellidos"}),
            "email": forms.EmailInput(attrs={"class": "i-input", "placeholder": "Correo electrónico"}),
        }

    def clean(self):
        cleaned = super().clean()
        pw1 = cleaned.get("password")
        pw2 = cleaned.get("confirmar_password")
        if pw1 != pw2:
            raise forms.ValidationError("⚠️ Las contraseñas no coinciden.")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data["password"]
        user.set_password(password)
        if commit:
            user.save()
        return user
