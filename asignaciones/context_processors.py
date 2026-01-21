from .models import Anuncio
from django.db import models
from django.utils import timezone
from django.db.models import Q

def anuncios_context(request):
    if not request.user.is_authenticated:
        return {}

    user = request.user
    ahora = timezone.now()

    anuncios_no_leidos = (
        Anuncio.objects
        .exclude(lecturas__usuario=user)
        .exclude(eliminaciones__usuario=user)
        .filter(
            Q(destinatario=user)
            | Q(grupo_destino__in=user.groups.all())
            | Q(tipo="general"),
            Q(fecha_inicio__lte=ahora) | Q(fecha_inicio__isnull=True),
            Q(fecha_fin__gte=ahora) | Q(fecha_fin__isnull=True),
        )
        .distinct()
        .count()
    )

    return {
        "contador_anuncios": anuncios_no_leidos
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
