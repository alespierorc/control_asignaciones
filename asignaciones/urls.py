from django.urls import path
from . import views

app_name = "asignaciones"

urlpatterns = [
    # Home / Login
    path("", views.login_demo, name="login"),
    path("home/", views.home_selector, name="home_selector"),

    # Homes
    path("home/supervisor/", views.home_supervisor, name="home_supervisor"),
    path("home/coordinador/", views.home_coordinador, name="home_coordinador"),
    path("home/admin/", views.home_admin, name="home_admin"),

    # Chips topbar
    path("reportes/", views.reportes, name="reportes"),
    path("anuncios/", views.anuncios, name="anuncios"),
    path("bandeja/", views.bandeja, name="bandeja"),

    # ============================================================
    # SUPERVISOR
    # ============================================================

    path("supervisor/panel/", views.supervisor_panel, name="supervisor_panel"),
    path("supervisor/registrar/", views.supervisor_registrar, name="supervisor_registrar"),
    path("supervisor/revisar/", views.supervisor_revisar, name="supervisor_revisar"),
    path("supervisor/estado/", views.estado_expediente, name="supervisor_estado"),

    # ✅ Nueva ruta: concluir expediente manualmente
    path("supervisor/concluir/<int:pk>/", views.concluir_expediente, name="supervisor_concluir"),

    # ✅ Nueva ruta AJAX para autocompletado en N° SIGED y Carta Línea
    path("ajax/autocomplete/", views.autocomplete_expediente, name="autocomplete_expediente"),

    # ============================================================
    # COORDINADOR
    # ============================================================
    path("coordinador/", views.coordinador_menu, name="coordinador_menu"),
    path("coordinador/registrar/", views.coordinador_registrar, name="coordinador_registrar"),
    path("coordinador/revisar/", views.coordinador_revisar, name="coordinador_revisar"),

    # ============================================================
    # ADMIN (sin chocar con /admin/ de Django)
    # ============================================================
    path("panel-admin/general/", views.admin_general_menu, name="admin_general_menu"),
    path("panel-admin/simple/", views.admin_simple_menu, name="admin_simple_menu"),
    path("panel-admin/general/revisar/", views.admin_general_revisar, name="admin_general_revisar"),
    path("panel-admin/general/descargar/", views.admin_general_descargar, name="admin_general_descargar"),
    path("panel-admin/simple/revisar/", views.admin_simple_revisar, name="admin_simple_revisar"),
    path("panel-admin/simple/descargar/", views.admin_simple_descargar, name="admin_simple_descargar"),

    # AJAX
    path("ajax/autocomplete/", views.ajax_autocomplete, name="ajax_autocomplete"),
    path("ajax/registrar-visita/", views.ajax_registrar_visita, name="ajax_registrar_visita"),
    path("ajax/actualizar-estado/", views.ajax_actualizar_estado, name="ajax_actualizar_estado"),
    
    # Anuncios
    path("anuncios/", views.anuncios, name="anuncios"),
    path("anuncios/crear/", views.crear_anuncio, name="crear_anuncio"),
]
