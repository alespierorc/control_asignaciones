# ============================================================
#                      URLS.PY - SERMINCO
# ============================================================
# Sistema corporativo de control de asignaciones
# Estructurado por roles:
# - AdministradorLider
# - Administrador
# - Coordinador
# - Supervisor
# ============================================================

from django.urls import path
from . import views
from django.contrib.auth import views as auth_views


app_name = "asignaciones"

urlpatterns = [
    # ============================================================
    # AUTENTICACIÓN
    # ============================================================
    path("login/", views.login_demo, name="login"),  # Página de login personalizada
    path("logout/", views.logout_view, name="logout"),  # Logout con POST seguro
    path("", views.home_router, name="home_router"),  # Redirección automática según rol

    # ============================================================
    # DASHBOARDS / PANELES PRINCIPALES
    # ============================================================
    path("home/supervisor/", views.home_supervisor, name="home_supervisor"),
    path("home/coordinador/", views.coordinador_menu, name="home_coordinador"),
    path("home/admin-lider/", views.admin_lider_menu, name="home_admin_lider"),
    path("home/admin/", views.admin_menu, name="home_admin"),

    # ============================================================
    # MÓDULOS COMUNES
    # ============================================================
    path("bandeja/", views.bandeja, name="bandeja"),
    path("anuncios/", views.anuncios, name="anuncios"),
    path("anuncios/crear/", views.crear_anuncio, name="crear_anuncio"),

    # ============================================================
    # SUPERVISOR
    # ============================================================
    path("supervisor/", views.supervisor_panel, name="supervisor_panel"),
    path("supervisor/registrar/", views.supervisor_registrar, name="supervisor_registrar"),
    path("supervisor/estado/", views.estado_expediente, name="supervisor_estado"),

    # ============================================================
    # COORDINADOR
    # ============================================================
    path("coordinador/", views.coordinador_menu, name="coordinador_menu"),
    path("coordinador/registrar/", views.coordinador_registrar, name="coordinador_registrar"),
    path("coordinador/revisar/", views.coordinador_revisar, name="coordinador_revisar"),

    # ============================================================
    # ADMINISTRADORES
    # ============================================================
    # 🔸 ADMINISTRADOR LÍDER
    path("panel-admin/lider/", views.admin_lider_menu, name="admin_lider_menu"),
    path("panel-admin/lider/revisar/", views.admin_lider_revisar, name="admin_lider_revisar"),
    path("panel-admin/lider/descargar/", views.admin_lider_descargar, name="admin_lider_descargar"),
    path("panel-admin/lider/descargar/excel/", views.admin_lider_descargar_excel, name="admin_lider_descargar_excel"),


    # 🔹 ADMINISTRADOR
    path("panel-admin/", views.admin_menu, name="admin_menu"),
    path("panel-admin/revisar/", views.admin_revisar, name="admin_revisar"),
    path("panel-admin/descargar/", views.admin_descargar, name="admin_descargar"),
    path("panel-admin/lider/catalogos/", views.admin_lider_catalogos, name="admin_lider_catalogos"), 
    path("panel-admin/descargar/excel/", views.admin_descargar_excel, name="admin_descargar_excel"),


    # ============================================================
    # GESTIÓN DE USUARIOS
    # ============================================================
    path("usuarios/", views.lista_usuarios, name="lista_usuarios"),
    path("usuarios/crear/", views.crear_usuario, name="crear_usuario"),
    path("usuarios/editar/<int:user_id>/", views.editar_usuario, name="editar_usuario"),
    path("usuarios/eliminar/<int:user_id>/", views.eliminar_usuario, name="eliminar_usuario"),

    # ============================================================
    # ENDPOINTS AJAX
    # ============================================================
    path("ajax/autocomplete/", views.ajax_autocomplete, name="ajax_autocomplete"),
    path("ajax/registrar-visita/", views.ajax_registrar_visita, name="ajax_registrar_visita"),
    path("ajax/actualizar-estado/", views.ajax_actualizar_estado, name="ajax_actualizar_estado"),

    path("reportes/", views.reportes, name="reportes"),
    path("reportes/json/", views.reportes_json, name="reportes_json"),
    path("anuncios/metricas/", views.anuncios_metricas, name="anuncios_metricas"),
    path("reportes/exportar/", views.exportar_excel, name="exportar_excel"),
    path("anuncios/no-leidos/", views.anuncios_no_leidos, name="anuncios_no_leidos"),
    path("anuncios/marcar-leido/<int:pk>/",views.marcar_anuncio_leido,name="marcar_anuncio_leido"),
    path("anuncios/eliminar/<int:pk>/",views.eliminar_anuncio,name="eliminar_anuncio"),

    

]
