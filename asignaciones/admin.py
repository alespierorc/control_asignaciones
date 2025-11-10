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
    list_display = ("siged", "codigo", "supervisor", "tipo_supervision", "estado", "visita_decision", "fecha_visita", "updated_at")
    search_fields = ("siged", "codigo")
    list_filter = ("estado", "tipo_supervision", "visita_decision", "oficina")
    ordering = ("-updated_at",)
