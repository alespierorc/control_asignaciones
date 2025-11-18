from django.contrib import admin
from .models import OficinaRegional, Contrato, Expediente, Mensaje, Anuncio


# ============================================================
#                 ADMINISTRADOR: OFICINAS
# ============================================================
@admin.register(OficinaRegional)
class OficinaRegionalAdmin(admin.ModelAdmin):
    list_display = ("nombre",)
    search_fields = ("nombre",)


# ============================================================
#                 ADMINISTRADOR: CONTRATOS
# ============================================================
@admin.register(Contrato)
class ContratoAdmin(admin.ModelAdmin):
    list_display = ("numero", "oficina", "descripcion")
    search_fields = ("numero", "descripcion")
    list_filter = ("oficina",)


# ============================================================
#                 ADMINISTRADOR: EXPEDIENTES
# ============================================================
@admin.register(Expediente)
class ExpedienteAdmin(admin.ModelAdmin):
    list_display = (
        "siged",
        "codigo",
        "supervisor",
        "tipo_supervision",
        "estado",
        "visita_decision",
        "fecha_asignacion",
        "fecha_visita",
        "fecha_derivacion",
    )
    search_fields = ("siged", "codigo", "supervisor__username")
    list_filter = (
        "estado",
        "tipo_supervision",
        "tipo_documento",
        "visita_decision",
        "oficina",
        "contrato",
    )
    ordering = ("-fecha_asignacion",)
    date_hierarchy = "fecha_asignacion"


# ============================================================
#                 ADMINISTRADOR: MENSAJES
# ============================================================
@admin.register(Mensaje)
class MensajeAdmin(admin.ModelAdmin):
    list_display = ("asunto", "remitente", "destinatario", "creado_en")
    search_fields = ("asunto", "remitente__username", "destinatario__username")
    list_filter = ("creado_en",)
    ordering = ("-creado_en",)


# ============================================================
#                 ADMINISTRADOR: ANUNCIOS
# ============================================================
@admin.register(Anuncio)
class AnuncioAdmin(admin.ModelAdmin):
    list_display = ("titulo", "destino", "creador", "creado_en")
    search_fields = ("titulo", "contenido", "creador__username")
    list_filter = ("destino", "creado_en")
    ordering = ("-creado_en",)
