from django.db.models import Count
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test

from .models import Expediente
from .forms import ProgramarVisitaForm, ConcluirForm


# ============================================================
#                   HELPERS (roles y grupos)
# ============================================================

def has_group(user, name: str) -> bool:
    """True si el usuario pertenece al grupo 'name'."""
    return user.is_authenticated and user.groups.filter(name=name).exists()


def user_role(user):
    """
    Rol mayoritario para router futuro.
    Devuelve: 'ADMIN', 'COORD', 'SUP' o None.
    """
    if user.is_superuser or has_group(user, "AdminGeneral") \
       or has_group(user, "Administracion") or has_group(user, "Administración"):
        return "ADMIN"
    if has_group(user, "Coordinador"):
        return "COORD"
    if has_group(user, "Supervisor"):
        return "SUP"
    return None


def is_in(group_name):
    """Decorator helper: permite si es superuser o del grupo indicado."""
    def check(u):
        return u.is_superuser or has_group(u, group_name)
    return check


# ============================================================
#                     DEMO (sin auth real)
# ============================================================

def login_demo(request):
    """
    Login de prueba (sin validar credenciales).
    Si viene ?next=/ruta/, redirige ahí; si no, al selector de homes.
    """
    if request.method == "POST":
        next_url = request.POST.get("next") or request.GET.get("next")
        return redirect(next_url or "asignaciones:home_selector")
    return render(request, "registration/login.html")


def home_selector(request):
    """Menú neutro para elegir home por rol."""
    return render(request, "roles/home_selector.html")


# ---------------------- Homes DEMO --------------------------

def home_supervisor(request):
    return render(request, "roles/supervisor_home.html")


def home_coordinador(request):
    """
    El Home de Coordinador redirige a su MENÚ (ASIGNACIONES + 2 botones).
    """
    return redirect("asignaciones:coordinador_menu")
    # Alternativa directa:
    # return render(request, "coordinador/menu.html")


def home_admin(request):
    """
    Home de Admin (selector de sub-roles).
    Plantilla: templates/roles/admin_home.html
    """
    return render(request, "roles/admin_home.html")


# ------------------- Chips del topbar -----------------------

def reportes(request):
    return render(request, "misc/reportes.html")


def anuncios(request):
    return render(request, "misc/anuncios.html")


def bandeja(request):
    return render(request, "misc/bandeja.html")


# ============================================================
#                    Supervisor (DEMO)
# ============================================================

def supervisor_panel(request):
    return render(request, "supervisor/panel.html")


def supervisor_registrar_demo(request):
    return render(request, "supervisor/registrar.html")


def supervisor_revisar_demo(request):
    return render(request, "supervisor/revisar.html")


def supervisor_estado_demo(request):
    return render(request, "supervisor/estado.html")


# ============================================================
#                    Coordinador (DEMO)
# ============================================================

def coordinador_menu(request):
    """Panel principal del Coordinador (ASIGNACIONES + 2 botones)."""
    return render(request, "coordinador/menu.html")


def coordinador_registrar(request):
    """Pantalla demo: Registrar expedientes."""
    return render(request, "coordinador/registrar.html")


def coordinador_revisar(request):
    """Pantalla demo: Revisar expediente."""
    return render(request, "coordinador/revisar.html")


# ============================================================
#                      ADMIN (DOS SUB-ROLES)
#  Prefijo de URL recomendado: /panel-admin/ (evita conflicto
#  con /admin/ del site admin de Django)
# ============================================================

# -------- Menús --------

def admin_general_menu(request):
    """
    Sub-rol: Administrador GENERAL.
    Accede a acciones propias y a paneles de Supervisor/Coordinador.
    """
    return render(request, "admin/menu_general.html")


def admin_simple_menu(request):
    """
    Sub-rol: Administración (SIMPLE).
    Acciones: Revisar expediente y Descargar.
    """
    return render(request, "admin/menu_simple.html")


# -------- Acciones (GENERAL) --------

def admin_general_revisar(request):
    return render(request, "admin/revisar_general.html")


def admin_general_descargar(request):
    return render(request, "admin/descargar_general.html")


# -------- Acciones (SIMPLE) --------

def admin_simple_revisar(request):
    return render(request, "admin/revisar_simple.html")


def admin_simple_descargar(request):
    return render(request, "admin/descargar_simple.html")


# ============================================================
#      Rutas protegidas (para cuando actives autenticación)
# ============================================================

@login_required
def home_router_protegido(request):
    """
    Cuando actives auth real: envía al home según rol.
    """
    role = user_role(request.user)
    if role == "SUP":
        return redirect("asignaciones:home_supervisor_protegido")
    if role == "COORD":
        return redirect("asignaciones:home_coordinador_protegido")
    if role == "ADMIN":
        return redirect("asignaciones:home_admin_protegido")
    # Sin rol: landing simple
    return render(request, "home.html")


# --- Protegidos por rol ---

@login_required
@user_passes_test(is_in("Supervisor"), login_url="login")
def home_supervisor_protegido(request):
    stats = (
        Expediente.objects
        .filter(supervisor=request.user)
        .values("estado").annotate(total=Count("id")).order_by("estado")
    )
    return render(request, "roles/supervisor_home.html", {"stats": stats})


@login_required
@user_passes_test(is_in("Coordinador"), login_url="login")
def home_coordinador_protegido(request):
    # En este caso, lo redirigimos al panel real del coordinador
    return redirect("asignaciones:coordinador_menu")


@login_required
def home_admin_protegido(request):
    """
    Decide a qué sub-rol de Admin enviar:
    - superuser o grupo 'AdminGeneral' => admin_general_menu
    - grupos 'Administracion' / 'Administración' => admin_simple_menu
    """
    if request.user.is_superuser or has_group(request.user, "AdminGeneral"):
        return redirect("asignaciones:admin_general_menu")

    if has_group(request.user, "Administracion") or has_group(request.user, "Administración"):
        return redirect("asignaciones:admin_simple_menu")

    # Si no pertenece a grupos esperados, muestra el selector
    return render(request, "roles/admin_home.html")


# ============================================================
#     Supervisor (real, con auth) — listo para futuro
# ============================================================

@login_required
@user_passes_test(is_in("Supervisor"), login_url="login")
def supervisor_menu(request):
    return render(request, "asignaciones/supervisor_menu.html")


@login_required
@user_passes_test(is_in("Supervisor"), login_url="login")
def supervisor_registrar_visita(request):
    """
    Registro de datos de visita: expedientes sin fecha_visita.
    """
    qs = (
        Expediente.objects
        .filter(supervisor=request.user, fecha_visita__isnull=True)
        .order_by("-updated_at")
    )
    return render(
        request,
        "asignaciones/mis_expedientes.html",
        {"expedientes": qs, "title": "Registrar datos de visita"},
    )


@login_required
@user_passes_test(is_in("Supervisor"), login_url="login")
def _legacy_evaluar_to_registrar(request):
    return redirect("asignaciones:supervisor_registrar_visita")


@login_required
@user_passes_test(is_in("Supervisor"), login_url="login")
def supervisor_revisar(request):
    qs = (
        Expediente.objects
        .filter(supervisor=request.user, estado="PENDIENTE")
        .order_by("-updated_at")
    )
    return render(
        request,
        "asignaciones/mis_expedientes.html",
        {"expedientes": qs, "title": "Revisar"},
    )


@login_required
@user_passes_test(is_in("Supervisor"), login_url="login")
def estado_expediente(request):
    stats = (
        Expediente.objects
        .filter(supervisor=request.user)
        .values("estado").annotate(total=Count("id")).order_by("estado")
    )
    return render(request, "asignaciones/estado_expediente.html", {"stats": stats})


@login_required
@user_passes_test(is_in("Supervisor"), login_url="login")
def programar_visita(request, pk):
    exp = get_object_or_404(Expediente, pk=pk, supervisor=request.user)

    if exp.estado == "CONCLUIDO":
        messages.warning(request, "Este expediente ya está concluido.")
        return redirect("asignaciones:supervisor_registrar_visita")

    if request.method == "POST":
        form = ProgramarVisitaForm(request.POST, instance=exp)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.estado = "PENDIENTE"
            obj.save()
            messages.success(request, "Visita programada correctamente.")
            return redirect("asignaciones:supervisor_registrar_visita")
        messages.error(request, "Corrige los errores del formulario.")
    else:
        form = ProgramarVisitaForm(instance=exp)

    return render(request, "asignaciones/programar_visita.html", {"form": form, "exp": exp})


@login_required
@user_passes_test(is_in("Supervisor"), login_url="login")
def concluir_expediente(request, pk):
    exp = get_object_or_404(Expediente, pk=pk, supervisor=request.user)

    if exp.estado == "CONCLUIDO":
        messages.info(request, "El expediente ya se encontraba concluido.")
        return redirect("asignaciones:supervisor_revisar")

    if not exp.fecha_visita:
        messages.warning(request, "Debes programar/realizar la visita antes de concluir.")
        return redirect("asignaciones:programar_visita", pk=exp.pk)

    if request.method == "POST":
        form = ConcluirForm(request.POST, instance=exp)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.estado = "CONCLUIDO"
            obj.save()
            messages.success(request, "Expediente concluido correctamente.")
            return redirect("asignaciones:supervisor_revisar")
        messages.error(request, "Corrige los errores del formulario.")
    else:
        form = ConcluirForm(instance=exp)

    return render(request, "asignaciones/concluir.html", {"form": form, "exp": exp})
