from django.db.models import Count
from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from .models import Expediente, Contrato, OficinaRegional, Mensaje, Anuncio
from django.db import models
from .forms import SupervisorEstadoForm
from .forms import SupervisorVisitaForm

import datetime

from .models import Expediente
from .forms import (
    ProgramarVisitaForm,
    ConcluirForm,
    CoordinadorRegistroForm,  
)

# ============================================================
#                      Helpers de roles
# ============================================================

def has_group(user, name: str) -> bool:
    return user.is_authenticated and user.groups.filter(name=name).exists()


def user_role(user):
    """
    Devuelve un string con el rol principal del usuario.
    """
    if user.is_superuser or has_group(user, "AdminGeneral") or has_group(user, "Administracion") or has_group(user, "Administración"):
        return "ADMIN"
    if has_group(user, "Coordinador"):
        return "COORD"
    if has_group(user, "Supervisor"):
        return "SUP"
    return None


def is_in(group_name):
    """
    Helper para user_passes_test: verifica si el usuario es superuser
    o pertenece al grupo indicado.
    """
    def check(u):
        return u.is_superuser or has_group(u, group_name)
    return check


# ============================================================
#        Listas fijas para selects (ajusta según tu data)
# ============================================================

# Contratos disponibles para el coordinador
CONTRATOS_CHOICES = [
    "CONTRATO 001-2025",
    "CONTRATO 002-2025",
    "CONTRATO 003-2025",
   
]

# Tipos de supervisión
TIPOS_SUPERVISION_CHOICES = [
    ("ORDINARIA", "Supervisión ordinaria"),
    ("INOPINADA", "Inspección inopinada"),
    ("ESPECIAL", "Supervisión especial"),
    ("OTRO", "Otro"),
]

# Tipos de documento
TIPOS_DOCUMENTO_CHOICES = [
    ("OFICIO", "Oficio múltiple"),
    ("FICHA", "Ficha de registro de hidrocarburos"),
    ("INFORME", "Informe técnico"),
    ("OTRO", "Otro"),
]


# ============================================================
#                           DEMO / Homes
# ============================================================

def login_demo(request):
    """
    Login de prueba (sin validar credenciales reales).
    Si viene ?next=/ruta/, redirige ahí; si no, al selector de homes.
    """
    if request.method == "POST":
        next_url = request.POST.get("next") or request.GET.get("next")
        return redirect(next_url or "asignaciones:home_selector")
    return render(request, "registration/login.html")


def home_selector(request):
    """
    Menú neutro para elegir home por rol.
    (Se llama desde la ruta 'home/' en tus urls.)
    """
    return render(request, "roles/home_selector.html")


def home_supervisor(request):
    return render(request, "roles/supervisor_home.html")


def home_coordinador(request):
  
    return redirect("asignaciones:coordinador_menu")


def home_admin(request):
    return render(request, "roles/admin_home.html")


# Chips del topbar
def reportes(request):
    return render(request, "misc/reportes.html")


def anuncios(request):
    return render(request, "misc/anuncios.html")


def bandeja(request):
    return render(request, "misc/bandeja.html")


# ============================================================
#                         Supervisor
# ============================================================
def supervisor_panel(request):
    """Panel principal del supervisor (demo, sin login)."""
    return render(request, "supervisor/panel.html")

def supervisor_registrar(request):
    """
    Registrar datos de visita:
    - Select de N.º SIGED con expedientes asignados al supervisor logueado.
    - Guarda visita (Sí/No) y fecha.
    """
    if request.user.is_authenticated:
        qs = Expediente.objects.filter(supervisor=request.user)
    else:
        qs = Expediente.objects.all()

    expedientes = qs.order_by("-created_at")

    form = SupervisorVisitaForm(request.POST or None)
    form.set_siged_choices(expedientes)

    if request.method == "POST":
        siged_value = (request.POST.get("siged_choices") or "").strip()
        visita_val = (request.POST.get("visita_decision") or "").strip().upper()
        fecha_val = (request.POST.get("fecha_visita") or "").strip()

        if not siged_value:
            messages.error(request, "Selecciona un N.° SIGED.")
        elif visita_val not in ("SI", "NO"):
            messages.error(request, "Elige si habrá visita (Sí o No).")
        elif not fecha_val:
            messages.error(request, "Selecciona la fecha de visita.")
        else:
            lookup = {"siged": siged_value}
            if request.user.is_authenticated:
                lookup["supervisor"] = request.user

            exp = get_object_or_404(Expediente, **lookup)
            exp.visita_decision = visita_val
            exp.fecha_visita = fecha_val
            exp.estado = "PENDIENTE"
            exp.save()
            messages.success(request, f"✅ Visita registrada para el expediente {exp.siged}.")
            return redirect("asignaciones:supervisor_registrar")

    return render(
        request,
        "supervisor/registrar.html",
        {
            "form": form,
            "expedientes": expedientes,
        },
    )



def supervisor_revisar(request):
    """
    Lista los expedientes en proceso, pendientes o concluidos.
    (Demo sin login)
    """
    expedientes = Expediente.objects.all().order_by("-fecha_asignacion")
    return render(
        request,
        "supervisor/revisar.html",
        {"expedientes": expedientes},
    )


def estado_expediente(request):
    """
    Vista: Estado de Expedientes del Supervisor
    - Muestra los expedientes asignados a él.
    - Permite modificar fecha_derivacion, concluir y observaciones.
    """
    # Filtra los expedientes dependiendo si hay login o no
    if request.user.is_authenticated:
        expedientes = Expediente.objects.filter(supervisor=request.user)
    else:
        expedientes = Expediente.objects.all()

    form = SupervisorEstadoForm()

    if request.method == "POST":
        exp_id = request.POST.get("expediente")
        if not exp_id:
            messages.error(request, "Debes seleccionar un expediente antes de guardar.")
            return redirect("asignaciones:supervisor_estado")

        exp = get_object_or_404(expedientes, id=exp_id)
        form = SupervisorEstadoForm(request.POST, instance=exp)

        if form.is_valid():
            expediente = form.save(commit=False)

            # Si el supervisor marca concluido → actualiza el estado
            if expediente.concluido:
                expediente.estado = "CONCLUIDO"
            else:
                # Si desmarca, vuelve al estado anterior si aplica
                expediente.estado = "EN_PROCESO"

            expediente.save()
            messages.success(request, f"✅ Expediente {expediente.siged} actualizado correctamente.")
            return redirect("asignaciones:supervisor_estado")
        else:
            messages.error(request, "⚠️ Corrige los errores antes de guardar.")

    return render(
        request,
        "supervisor/estado.html",
        {"expedientes": expedientes, "form": form},
    )


def concluir_expediente(request, pk):
    """
    Marca el expediente como concluido (requiere fecha_visita).
    """
    exp = get_object_or_404(Expediente, pk=pk)

    if exp.estado == "CONCLUIDO":
        messages.info(request, "El expediente ya se encontraba concluido.")
        return redirect("asignaciones:supervisor_revisar")

    if not getattr(exp, "fecha_visita", None):
        messages.warning(request, "Debes registrar la visita antes de concluir.")
        return redirect("asignaciones:supervisor_registrar")

    if request.method == "POST":
        form = ConcluirForm(request.POST, instance=exp)
        if form.is_valid():
            exp = form.save(commit=False)
            exp.estado = "CONCLUIDO"
            exp.save()
            messages.success(request, f"✅ El expediente {exp.siged} ha sido concluido.")
            return redirect("asignaciones:supervisor_revisar")
    else:
        form = ConcluirForm(instance=exp)

    return render(
        request,
        "asignaciones/concluir.html",
        {"form": form, "exp": exp},
    )

# ============================================================
#                         Coordinador
# ============================================================
# ============================================================
#                         Coordinador
# ============================================================
# ============================================================
#                         Coordinador
# ============================================================
def coordinador_menu(request):
    return render(request, "coordinador/menu.html")


def coordinador_registrar(request):
    """
    Registro de expedientes para Coordinador.
    Cada envío del formulario crea un nuevo Expediente (un 'Item').

    Campos requeridos:
      1. contrato
      2. siged (obligatorio)
      3. carta_linea (obligatorio)
      4. codigo (Código OSINERGMIN)
      5. codigo_actividad
      6. razon_social
      7. tipo_supervision
      8. tipo_documento
      9. oficina
      10. supervisor
      11. visita_decision (SI/NO)
      12. fecha_asignacion
    """

    # Datos para selects
    supervisors = (
        User.objects.filter(groups__name="Supervisor")
        .order_by("first_name", "last_name")
        .distinct()
    )
    contratos = Contrato.objects.select_related("oficina").order_by("numero")
    oficinas = OficinaRegional.objects.all().order_by("nombre")

    # Estructura base de datos (para mantener valores si hay error)
    data = {
        "contrato": "",
        "siged": "",
        "carta_linea": "",
        "codigo": "",
        "codigo_actividad": "",
        "razon_social": "",
        "tipo_supervision": "",
        "tipo_documento": "",
        "oficina": "",
        "supervisor_id": "",
        "visita_decision": "NO",
        "fecha_asignacion": "",
    }

    if request.method == "POST":
        # Capturar datos
        for key in data.keys():
            data[key] = (request.POST.get(key) or "").strip()

        errors = []

        # =======================
        # VALIDACIONES BÁSICAS
        # =======================
        if not data["siged"]:
            errors.append("El N.º SIGED es obligatorio.")
        if not data["carta_linea"]:
            errors.append("La carta de línea es obligatoria.")
        if not data["razon_social"]:
            errors.append("La razón social es obligatoria.")

        supervisor_obj = None
        if data["supervisor_id"]:
            supervisor_obj = supervisors.filter(id=data["supervisor_id"]).first()
            if supervisor_obj is None:
                errors.append("Selecciona un supervisor válido.")

        if data["visita_decision"] not in ("SI", "NO"):
            data["visita_decision"] = "NO"

        # Fecha
        fecha_asignacion = None
        if data["fecha_asignacion"]:
            try:
                fecha_asignacion = datetime.date.fromisoformat(data["fecha_asignacion"])
            except ValueError:
                errors.append("La fecha de asignación no tiene un formato válido (AAAA-MM-DD).")
        else:
            errors.append("Debes seleccionar una fecha de asignación.")

        # =======================
        # GUARDAR O MOSTRAR ERRORES
        # =======================
        if errors:
            for e in errors:
                messages.error(request, e)
        else:
            Expediente.objects.create(
                contrato_id=data["contrato"] or None,
                siged=data["siged"],
                carta_linea=data["carta_linea"],
                codigo=data["codigo"] or None,
                codigo_actividad=data["codigo_actividad"] or None,
                razon_social=data["razon_social"] or "",
                tipo_supervision=data["tipo_supervision"] or None,
                tipo_documento=data["tipo_documento"] or None,
                oficina_id=data["oficina"] or None,
                supervisor=supervisor_obj,
                visita_decision=data["visita_decision"],
                fecha_asignacion=fecha_asignacion,
                estado="EN_PROCESO",
            )
            messages.success(request, "✅ Expediente registrado correctamente.")
            return redirect("asignaciones:coordinador_registrar")

    context = {
        "supervisores": supervisors,
        "oficinas": oficinas,
        "contratos": contratos,
        "data": data,
        "tipos_supervision_choices": [
            ("ORDINARIA", "Supervisión ordinaria"),
            ("INOPINADA", "Inspección inopinada"),
            ("ESPECIAL", "Supervisión especial"),
            ("OTRO", "Otro"),
        ],
        "tipos_documento_choices": [
            ("OFICIO", "Oficio múltiple"),
            ("FICHA", "Ficha de registro de hidrocarburos"),
            ("INFORME", "Informe técnico"),
            ("OTRO", "Otro"),
        ],
    }

    return render(request, "coordinador/registrar.html", context)


def coordinador_revisar(request):
    """Pantalla de revisión de expedientes para el coordinador."""
    qs = Expediente.objects.select_related("supervisor", "contrato", "oficina").order_by("-created_at")

    # Filtros
    contrato_id = request.GET.get("contrato")
    siged = request.GET.get("siged", "").strip()

    if contrato_id:
        qs = qs.filter(contrato_id=contrato_id)
    if siged:
        qs = qs.filter(siged__icontains=siged)

    contratos = Contrato.objects.select_related("oficina").order_by("numero")

    return render(request, "coordinador/revisar.html", {
        "expedientes": qs,
        "contratos": contratos,
    })
# ============================================================
#                         Admin / Paneles
# ============================================================

def admin_general_menu(request):
    return render(request, "admin/general_menu.html")


def admin_simple_menu(request):
    return render(request, "admin/simple_menu.html")


def admin_general_revisar(request):
    return render(request, "admin/general_revisar.html")


def admin_general_descargar(request):
    return render(request, "admin/general_descargar.html")


def admin_simple_revisar(request):
    return render(request, "admin/simple_revisar.html")


def admin_simple_descargar(request):
    return render(request, "admin/simple_descargar.html")

# ============================================================
#                  BANDEJA DE ENTRADA (MENSAJES)
# ============================================================

def bandeja(request):
    """Bandeja de entrada y envío de mensajes entre usuarios (modo libre sin login)."""

    # Evitar errores si no hay sesión activa
    usuario = getattr(request, 'user', None)
    if not usuario or not getattr(usuario, 'is_authenticated', False):
        class DummyUser:
            id = 0
            username = "Invitado"
            is_authenticated = False
        usuario = DummyUser()

    # Determinar rol (modo demo si no está logueado)
    role = user_role(usuario) if usuario.is_authenticated else "INVITADO"

    # Mostrar todos los mensajes en modo libre
    if usuario.is_authenticated:
        recibidos = Mensaje.objects.filter(destinatario=usuario).select_related("remitente")
    else:
        recibidos = Mensaje.objects.all().select_related("remitente")[:25]

    # Procesar envío de mensajes
    if request.method == "POST":
        dest_id = request.POST.get("destinatario")
        asunto = request.POST.get("asunto", "").strip()
        cuerpo = request.POST.get("cuerpo", "").strip()

        if not asunto or not cuerpo:
            messages.error(request, "Todos los campos son obligatorios.")
        else:
            # En modo libre no se valida destinatario
            destinatario = User.objects.filter(id=dest_id).first() if dest_id else None
            Mensaje.objects.create(
                remitente=usuario if hasattr(usuario, "id") else None,
                destinatario=destinatario,
                asunto=asunto or "(Sin asunto)",
                cuerpo=cuerpo,
            )
            messages.success(request, "Mensaje enviado correctamente.")
            return redirect("asignaciones:bandeja")

    usuarios = User.objects.all().order_by("username")

    return render(request, "misc/bandeja.html", {
        "recibidos": recibidos,
        "usuarios": usuarios,
        "role": role,
    })


# ============================================================
#                      ANUNCIOS INTERACTIVOS
# ============================================================

def anuncios(request):
    """Panel de anuncios interactivos. Modo libre sin login."""
    usuario = getattr(request, 'user', None)
    if not usuario or not getattr(usuario, 'is_authenticated', False):
        class DummyUser:
            id = 0
            username = "Invitado"
            is_authenticated = False
        usuario = DummyUser()

    role = user_role(usuario) if usuario.is_authenticated else "INVITADO"

    # Filtro según rol (modo libre: ver todo)
    if role == "SUP":
        anuncios = Anuncio.objects.filter(Q(destino="SUP") | Q(destino="AMBOS"))
    elif role == "COORD":
        anuncios = Anuncio.objects.filter(Q(destino="COORD") | Q(destino="AMBOS"))
    else:
        anuncios = Anuncio.objects.all()

    # Crear anuncio (permitido en modo libre también)
    if request.method == "POST":
        titulo = request.POST.get("titulo", "").strip()
        contenido = request.POST.get("contenido", "").strip()
        destino = request.POST.get("destino", "").strip()

        if not titulo or not contenido or not destino:
            messages.error(request, "Todos los campos son obligatorios.")
        elif destino not in ["SUP", "COORD", "AMBOS"]:
            messages.error(request, "Destino no válido.")
        else:
            Anuncio.objects.create(
                titulo=titulo,
                contenido=contenido,
                destino=destino,
                creador=usuario if hasattr(usuario, "id") else None,
            )
            messages.success(request, "Anuncio creado exitosamente.")
            return redirect("asignaciones:anuncios")

    return render(request, "misc/anuncios.html", {
        "anuncios": anuncios,
        "role": role,
    })


# ============================================================
#                          REPORTES
# ============================================================

def reportes(request):
    """Menú visual de reportes base (sin login)."""
    usuario = getattr(request, 'user', None)
    role = user_role(usuario) if usuario and getattr(usuario, 'is_authenticated', False) else "INVITADO"
    return render(request, "misc/reportes.html", {"role": role})

