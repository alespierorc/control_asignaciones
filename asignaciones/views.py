from django.db.models import Count
from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test

from .models import Expediente
from .forms import (
    ProgramarVisitaForm,
    ConcluirForm,
    SupervisorVisitaForm,
    CoordinadorRegistroForm,
)

# ===== Helpers roles =====
def has_group(user, name: str) -> bool:
    return user.is_authenticated and user.groups.filter(name=name).exists()

def user_role(user):
    if user.is_superuser or has_group(user, "AdminGeneral") or has_group(user, "Administracion") or has_group(user, "Administración"):
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

# ===== Demo / Homes =====
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

# ===== Supervisor =====
def supervisor_panel(request):
    return render(request, "supervisor/panel.html")

@login_required
@user_passes_test(is_in("Supervisor"), login_url="login")
def supervisor_registrar(request):
    # Expedientes del supervisor (para el select de SIGED)
    expedientes = (
        Expediente.objects.filter(supervisor=request.user)
        .order_by("-updated_at")
        .only("id", "siged", "codigo", "tipo_supervision", "estado")
    )

    form = SupervisorVisitaForm(request.POST or None)
    form.set_siged_choices(expedientes)

    if request.method == "POST":
        siged_value = (form.data.get("siged") or "").strip()
        visita_val = (form.data.get("visita_decision") or "").strip().upper()
        fecha_val = (form.data.get("fecha_visita") or "").strip()

        if not siged_value:
            messages.error(request, "Selecciona un N.° SIGED.")
        elif visita_val not in ("SI", "NO"):
            messages.error(request, "Elige si habrá visita: marca Sí o No.")
        elif not fecha_val:
            messages.error(request, "Selecciona la fecha de visita.")
        else:
            exp = get_object_or_404(Expediente, siged=siged_value, supervisor=request.user)
            exp.visita_decision = visita_val
            exp.fecha_visita = fecha_val
            exp.estado = "PENDIENTE"
            exp.save()
            messages.success(request, f"Visita registrada para el expediente {exp.siged}.")
            return redirect("asignaciones:supervisor_registrar")

    data_siged = [
        {"siged": e.siged, "codigo": e.codigo or "", "tipo": e.tipo_supervision, "estado": e.estado}
        for e in expedientes
    ]

    return render(
        request,
        "supervisor/registrar.html",
        {"form": form, "expedientes": expedientes, "data_siged": data_siged},
    )

@login_required(login_url="login")
@user_passes_test(is_in("Supervisor"), login_url="login")
def programar_visita_redirect(request, pk):
    # Ruta antigua compatible: reenvía al formulario nuevo con ?exp=pk (si lo necesitas)
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
    return render(request, "asignaciones/mis_expedientes.html", {"expedientes": qs, "title": "Revisar"})

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

# ===== Coordinador =====
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

# ===== Admin =====
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
