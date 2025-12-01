# ============================================================
# Middleware: ForceLogoutMiddleware
# ============================================================
# Este middleware asegura que, después del logout, Django no
# reutilice una sesión vieja por error o cookies persistentes.
# ============================================================

from django.shortcuts import redirect

class ForceLogoutMiddleware:
    """
    Middleware para asegurar que después del logout
    no se reinyecte sesión previa por cookies viejas.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Si hay cookie sessionid pero el usuario no está autenticado,
        # forzamos a limpiar la sesión para evitar reuso.
        if not request.user.is_authenticated and 'sessionid' in request.COOKIES:
            request.session.flush()
        return self.get_response(request)
