# ============================================================
#                DECORATORS.PY - SERMINCO
# ============================================================
# Decoradores personalizados para control de acceso por roles.
# ============================================================

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

def role_required(roles_permitidos):
    """
    Decorador que restringe el acceso a vistas basadas en grupos (roles).
    Ejemplo:
        @role_required(["AdministradorLider", "Coordinador"])
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, "⚠️ Debes iniciar sesión para acceder.")
                return redirect("login")

            # Verificar si el usuario pertenece a un grupo permitido
            if not request.user.groups.filter(name__in=roles_permitidos).exists():
                messages.error(request, "🚫 No tienes permiso para acceder a esta sección.")
                return redirect("login")

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
