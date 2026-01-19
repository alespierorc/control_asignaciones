from .models import Anuncio
from django.db import models

def anuncios_context(request):
    if not request.user.is_authenticated:
        return {}

    user = request.user

    anuncios_no_leidos = Anuncio.objects.filter(
        models.Q(destinatario=user) |
        models.Q(grupo_destino__in=user.groups.all()) |
        models.Q(tipo="general"),
        leido=False
    ).count()

    return {
        "anuncios_no_leidos": anuncios_no_leidos
    }

def permisos_navbar(request):
    if not request.user.is_authenticated:
        return {}

    user = request.user

    # Roles que NO deben ver reportes
    if user.groups.filter(name__in=["Supervisor", "Coordinador"]).exists():
        return {
            "mostrar_reportes": False
        }

    # Administrador y AdministradorLider (y cualquier otro futuro)
    if user.groups.filter(name__in=["Administrador", "AdministradorLider"]).exists():
        return {
            "mostrar_reportes": True
        }

    # Por defecto, no mostrar
    return {
        "mostrar_reportes": False
    }
