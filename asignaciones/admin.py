from django.contrib import admin
from .models import OficinaRegional, Contrato, Expediente

@admin.register(OficinaRegional)
class OficinaRegionalAdmin(admin.ModelAdmin):
    list_display = ("nombre",)
    search_fields = ("nombre",)

@admin.register(Contrato)
class ContratoAdmin(admin.ModelAdmin):
    list_display = ("numero", "oficina", "descripcion")
    search_fields = ("numero", "descripcion")
    list_filter = ("oficina",)

@admin.register(Expediente)
class ExpedienteAdmin(admin.ModelAdmin):
    # Ojo: aquí NO hay 'codigo'. Usamos campos reales del modelo.
    list_display = (
        "siged", "oficina", "contrato", "supervisor",
        "tipo_supervision", "visita", "estado", "fecha_visita",
    )
    list_filter = ("estado", "tipo_supervision", "oficina", "visita")
    search_fields = ("siged", "contrato__numero", "supervisor__username")
    autocomplete_fields = ("oficina", "contrato", "supervisor")
