from django.urls import path
from . import views

app_name = "asignaciones"

urlpatterns = [
    # Login demo
    path("", views.login_demo, name="login"),

    # Selector de home por rol
    path("home/", views.home_selector, name="home_selector"),

    # Homes (demo)
    path("home/supervisor/", views.home_supervisor, name="home_supervisor"),
    path("home/coordinador/", views.home_coordinador, name="home_coordinador"),
    path("home/admin/", views.home_admin, name="home_admin"),

    # Chips del topbar
    path("reportes/", views.reportes, name="reportes"),
    path("anuncios/", views.anuncios, name="anuncios"),
    path("bandeja/", views.bandeja, name="bandeja"),

    # Supervisor (demo)
    path("supervisor/panel/", views.supervisor_panel, name="supervisor_panel"),
    path("supervisor/registrar/", views.supervisor_registrar_demo, name="supervisor_registrar"),
    path("supervisor/revisar/", views.supervisor_revisar_demo, name="supervisor_revisar"),
    path("supervisor/estado/", views.supervisor_estado_demo, name="supervisor_estado"),

    # Coordinador (home + acciones)
    path("coordinador/", views.coordinador_menu, name="coordinador_menu"),
    path("coordinador/registrar/", views.coordinador_registrar, name="coordinador_registrar"),
    path("coordinador/revisar/", views.coordinador_revisar, name="coordinador_revisar"),

    # ============= ADMIN (NO usar /admin/ para evitar conflicto) =============
    # Home(s) Admin
    path("panel-admin/general/", views.admin_general_menu, name="admin_general_menu"),
    path("panel-admin/simple/", views.admin_simple_menu, name="admin_simple_menu"),

    # Admin GENERAL – acciones
    path("panel-admin/general/revisar/", views.admin_general_revisar, name="admin_general_revisar"),
    path("panel-admin/general/descargar/", views.admin_general_descargar, name="admin_general_descargar"),

    # Admin SIMPLE – acciones
    path("panel-admin/simple/revisar/", views.admin_simple_revisar, name="admin_simple_revisar"),
    path("panel-admin/simple/descargar/", views.admin_simple_descargar, name="admin_simple_descargar"),
]
