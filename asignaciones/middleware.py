# ============================================================
#            MIDDLEWARE DE SEGURIDAD POR ROLES - SERMINCO
# ============================================================
# Evita accesos no autorizados entre roles.
# Redirige a los paneles correctos con mensajes informativos.
# ============================================================

from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse

ROL_PATHS = {
    "AdministradorLider": [
        "/panel-admin/lider/",
        "/usuarios/",
        "/coordinador/",
        "/supervisor/",
        "/anuncios/",
        "/bandeja/",
    ],
    "Administrador": [
        "/panel-admin/",
        "/anuncios/",
        "/bandeja/",
    ],
    "Coordinador": [
        "/coordinador/",
        "/anuncios/",
        "/bandeja/",
    ],
    "Supervisor": [
        "/supervisor/",
        "/anuncios/",
        "/bandeja/",
    ],
}


from django.shortcuts import redirect
from django.urls import reverse

class RoleAccessMiddleware:
    """
    Controla el acceso a rutas según el rol del usuario.
    Evita bloqueos en logout o login.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Rutas que no deben ser filtradas por el middleware
        allowed_paths = [
            reverse("asignaciones:login"),
            reverse("asignaciones:logout"),
            reverse("asignaciones:home_router"),
            "/admin/",
            "/static/",
        ]

        # Ignora rutas que empiecen con los permitidos
        if any(request.path.startswith(path) for path in allowed_paths):
            return self.get_response(request)

        # Si el usuario no está autenticado → redirige al login
        if not request.user.is_authenticated:
            return redirect("asignaciones:login")

        # Si el usuario es supervisor y trata de acceder a una sección que no le corresponde
        if request.user.groups.filter(name="Supervisor").exists() and not request.path.startswith("/supervisor"):
            return redirect("asignaciones:supervisor_panel")

        return self.get_response(request)

