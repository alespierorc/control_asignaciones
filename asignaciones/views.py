from django.db.models import Count
from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test

from .models import Expediente
from .forms import ProgramarVisitaForm, ConcluirForm, CoordinadorRegistroForm

# ================== HELPERS (roles/grupos) ==================
def has_group(user, name: str) -> bool:
    return user.is_authenticated and user.groups.filter(name=name).exists()

def user_role(user):
    if user.is_superuser or has_group(user, "AdminGeneral") \
       or has_group(user, "Administracion") or has_group(user, "Administración"):
        return "ADMIN"
    if has_group(user, "Coordinador"):
        return "COORD"
    if has_group(user, "Supervisor"):
        return "SUP"
    return None

def is_in(group_name):
    def check(u):
        return u.is_superuser or has_group(u, group_name)
    return check

# ================== DEMO básicos ==================
def login_demo(request):
    if request.method == "POST":
        next_url = request.POST.get("next") or request.GET.get("next")
        return redirect(next_url or "asignaciones:home_selector")
    return render(request, "registration/login.html")

def home_selector(request):
    return render(request, "roles/home_selector.html")

def home_supervisor(request):
    return render(request, "roles/supervisor_home.html")

def home_coordinador(request):
    return redirect("asignaciones:coordinador_menu")

def home_admin(request):
    return render(request, "roles/admin_home.html")

def reportes(request):
    return render(request, "misc/reportes.html")

def anuncios(request):
    return render(request, "misc/anuncios.html")

def bandeja(request):
    return render(request, "misc/bandeja.html")

# ================== SUPERVISOR ==================
def supervisor_panel(request):
    return render(request, "supervisor/panel.html")

@login_required
@user_passes_test(is_in("Supervisor"), login_url="login")
def supervisor_registrar(request):
    """
    Pantalla unificada: Registrar datos de visita.
    - lista de expedientes del supervisor (N.º SIGED)
    - selecciona ?exp=<id> (o el primero)
    - guarda fecha_visita y visita (SI/NO), y deja estado PENDIENTE
    """
    expedientes_all = (
        Expediente.objects
        .filter(supervisor=request.user)  # quítalo si estás en DEMO
        .order_by("-updated_at")
        .only("id", "siged", "tipo_supervision")
    )

    selected_id = request.GET.get("exp")
    if not selected_id and expedientes_all:
        selected_id = str(expedientes_all[0].id)

    exp = get_object_or_404(Expediente, pk=selected_id) if selected_id else None
    form = ProgramarVisitaForm(request.POST or None, instance=exp) if exp else None

    if request.method == "POST" and exp and form and form.is_valid():
        obj = form.save(commit=False)
        # 'visita' llega desde el hidden del template (SI/NO)
        visita_val = request.POST.get("visita", "").upper().strip()
        if visita_val in ("SI", "NO"):
            obj.visita = visita_val
        obj.estado = "PENDIENTE"
        obj.save()
        messages.success(request, "Visita programada correctamente.")
        return redirect(f"{reverse('asignaciones:supervisor_registrar')}?exp={exp.id}")

    context = {"form": form, "exp": exp, "expedientes_all": expedientes_all}
    return render(request, "supervisor/registrar.html", context)

@login_required
@user_passes_test(is_in("Supervisor"), login_url="login")
def programar_visita_redirect(request, pk):
    # Compatibilidad con antigua ruta: redirige al flujo nuevo
    return redirect(f"{reverse('asignaciones:supervisor_registrar')}?exp={pk}")

def supervisor_revisar_demo(request):
    return render(request, "supervisor/revisar.html")

def supervisor_estado_demo(request):
    return render(request, "supervisor/estado.html")

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
def concluir_expediente(request, pk):
    exp = get_object_or_404(Expediente, pk=pk, supervisor=request.user)
    if exp.estado == "CONCLUIDO":
        messages.info(request, "El expediente ya se encontraba concluido.")
        return redirect("asignaciones:supervisor_revisar")
    if not exp.fecha_visita:
        messages.warning(request, "Debes programar/realizar la visita antes de concluir.")
        return redirect("asignaciones:programar_visita_redirect", pk=exp.pk)

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

# ================== COORDINADOR ==================
def coordinador_menu(request):
    return render(request, "coordinador/menu.html")

def coordinador_registrar(request):
    if request.method == "POST":
        form = CoordinadorRegistroForm(request.POST)
        if form.is_valid():
            exp = form.save(commit=False)
            if not exp.estado:
                exp.estado = "EN_PROCESO"
            exp.save()
            messages.success(request, "Expediente registrado correctamente.")
            return redirect("asignaciones:coordinador_menu")
        messages.error(request, "Corrige los errores e inténtalo nuevamente.")
    else:
        form = CoordinadorRegistroForm()
    return render(request, "coordinador/registrar.html", {"form": form})

def coordinador_revisar(request):
    return render(request, "coordinador/revisar.html")

# ================== ADMIN ==================
def admin_general_menu(request):
    return render(request, "admin/menu_general.html")

def admin_simple_menu(request):
    return render(request, "admin/menu_simple.html")

def admin_general_revisar(request):
    return render(request, "admin/revisar_general.html")

def admin_general_descargar(request):
    return render(request, "admin/descargar_general.html")

def admin_simple_revisar(request):
    return render(request, "admin/revisar_simple.html")

def admin_simple_descargar(request):
    return render(request, "admin/descargar_simple.html")
