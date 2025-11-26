from django.db.models import Count, Q
from django.urls import reverse
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from .models import Expediente, Contrato, OficinaRegional, Mensaje, Anuncio
from django.db import models
from .forms import SupervisorEstadoForm, SupervisorVisitaForm
import datetime
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


# ============================================================
#                           DEMO / Homes
# ============================================================

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


# ============================================================
#                         Supervisor
# ============================================================

# ============================================================
# Panel principal del supervisor
# ============================================================

def supervisor_panel(request):
    """
    Solo muestra el panel principal del supervisor.
    """
    return render(request, "supervisor/panel.html")


# ============================================================
# Registrar visita del expediente
# ============================================================

def supervisor_registrar(request):
    """
    Permite buscar un expediente (por N° SIGED o Carta Línea) y registrar su fecha real de visita.
    La actualización es mediante AJAX para reflejar cambios en tiempo real.
    """

    expedientes = (
        Expediente.objects.select_related("contrato", "oficina", "supervisor")
        .order_by("-fecha_asignacion", "-created_at")
    )

    resultados = []
    query_siged = request.GET.get("siged", "").strip()
    query_carta = request.GET.get("carta_linea", "").strip()

    # 🔹 Filtro de búsqueda
    if query_siged or query_carta:
        filtros = Q()
        if query_siged:
            filtros &= Q(siged__icontains=query_siged)
        if query_carta:
            filtros &= Q(carta_linea__icontains=query_carta)
        resultados = Expediente.objects.filter(filtros).select_related("contrato", "oficina", "supervisor")

        if not resultados.exists():
            messages.info(request, "No se encontraron expedientes con esos criterios.")

    # 🔹 AJAX: Registrar fecha de visita
    if request.headers.get("x-requested-with") == "XMLHttpRequest" and request.method == "POST":
        exp_id = request.POST.get("expediente_sel")
        fecha_val = request.POST.get("fecha_visita")

        if not exp_id or not fecha_val:
            return JsonResponse({
                "status": "error",
                "message": "Debes seleccionar un expediente y una fecha válida."
            })

        exp = get_object_or_404(Expediente, id=exp_id)
        exp.fecha_visita = fecha_val
        exp.estado = "EN_PROCESO"
        exp.save()

        return JsonResponse({
            "status": "success",
            "message": f"✅ Fecha de visita registrada correctamente para el expediente {exp.siged}.",
            "fecha_visita": exp.fecha_visita.strftime("%d/%m/%Y"),
            "siged": exp.siged,
        })

    context = {
        "expedientes": expedientes,
        "resultados": resultados,
        "query_siged": query_siged,
        "query_carta": query_carta,
    }

    return render(request, "supervisor/registrar.html", context)


# ============================================================
# Gestión de estado del expediente
# ============================================================

def estado_expediente(request):
    """
    Aquí manejo la actualización del estado de los expedientes:
    - Fecha de derivación
    - Observaciones
    - Estado: Concluido o En Proceso (mediante toggle)
    """

    expedientes = Expediente.objects.select_related("contrato", "oficina", "supervisor").order_by("-fecha_asignacion")
    resultados = []
    query_siged = request.GET.get("siged", "").strip()
    query_carta = request.GET.get("carta_linea", "").strip()

    # 🔹 Filtro de búsqueda
    if query_siged or query_carta:
        filtros = Q()
        if query_siged:
            filtros &= Q(siged__icontains=query_siged)
        if query_carta:
            filtros &= Q(carta_linea__icontains=query_carta)
        resultados = Expediente.objects.filter(filtros).select_related("contrato", "oficina", "supervisor")

        if not resultados.exists():
            messages.info(request, "No se encontraron expedientes con esos criterios.")

    # 🔹 AJAX: Actualización sin recargar
    if request.headers.get("x-requested-with") == "XMLHttpRequest" and request.method == "POST":
        exp_id = request.POST.get("expediente")
        fecha_deriv = request.POST.get("fecha_derivacion")
        estado_concluido = request.POST.get("estado") == "CONCLUIDO"
        observaciones = request.POST.get("observaciones", "").strip()

        if not exp_id:
            return JsonResponse({"status": "error", "message": "Debes seleccionar un expediente antes de guardar."})

        exp = get_object_or_404(Expediente, id=exp_id)

        if not fecha_deriv:
            return JsonResponse({"status": "error", "message": "Debes registrar una fecha de derivación válida."})

        exp.fecha_derivacion = fecha_deriv
        exp.observaciones = observaciones if observaciones else "-"
        exp.estado = "CONCLUIDO" if estado_concluido else "EN_PROCESO"
        exp.save()

        return JsonResponse({
            "status": "success",
            "message": f"✅ Expediente {exp.siged} actualizado correctamente.",
            "estado": exp.estado,
            "fecha_derivacion": exp.fecha_derivacion.strftime("%d/%m/%Y"),
        })

    context = {
        "expedientes": expedientes,
        "resultados": resultados,
        "query_siged": query_siged,
        "query_carta": query_carta,
    }

    return render(request, "supervisor/estado.html", context)


# ============================================================
# Endpoint AJAX para autocompletado
# ============================================================

def autocomplete_expediente(request):
    """
    Endpoint que devuelve coincidencias de N° SIGED o Carta Línea
    para el autocompletado en los formularios (usado por datalist).
    """
    field = request.GET.get("field")
    query = request.GET.get("q", "").strip()

    if not field or not query:
        return JsonResponse({"results": []})

    if field == "siged":
        results = list(Expediente.objects.filter(siged__icontains=query).values_list("siged", flat=True)[:10])
    elif field == "carta_linea":
        results = list(Expediente.objects.filter(carta_linea__icontains=query).values_list("carta_linea", flat=True)[:10])
    else:
        results = []

    return JsonResponse({"results": results})


# ============================================================
# Revisión general de expedientes
# ============================================================

def supervisor_revisar(request):
    """
    Muestra todos los expedientes disponibles para revisión general.
    """
    expedientes = (
        Expediente.objects.select_related("contrato", "oficina", "supervisor")
        .order_by("-fecha_asignacion")
    )
    return render(request, "supervisor/revisar.html", {"expedientes": expedientes})


# ============================================================
# Concluir expediente manualmente
# ============================================================

def concluir_expediente(request, pk):
    """
    Permite marcar manualmente un expediente como concluido,
    siempre que tenga una fecha de visita registrada.
    """
    exp = get_object_or_404(Expediente, pk=pk)

    if exp.estado == "CONCLUIDO":
        messages.info(request, "El expediente ya está concluido.")
        return redirect("asignaciones:supervisor_revisar")

    if not getattr(exp, "fecha_visita", None):
        messages.warning(request, "Debes registrar la fecha de visita antes de concluir.")
        return redirect("asignaciones:supervisor_registrar")

    if request.method == "POST":
        form = ConcluirForm(request.POST, instance=exp)
        if form.is_valid():
            exp = form.save(commit=False)
            exp.estado = "CONCLUIDO"
            exp.save()
            messages.success(request, f"✅ El expediente {exp.siged} ha sido marcado como concluido.")
            return redirect("asignaciones:supervisor_revisar")
    else:
        form = ConcluirForm(instance=exp)

    return render(request, "asignaciones/concluir.html", {"form": form, "exp": exp})


# ============================================================
#                         Coordinador
# ============================================================

def coordinador_menu(request):
    # Verifica si el usuario tiene permisos para crear anuncios
    puede_crear_anuncio = request.user.groups.filter(
        name__in=["Coordinador", "Administrador General", "Administrador Simple"]
    ).exists()

    return render(
        request,
        "coordinador/menu.html",
        {"puede_crear_anuncio": puede_crear_anuncio}
    )

def coordinador_registrar(request):
    supervisors = User.objects.filter(groups__name="Supervisor").order_by("first_name", "last_name").distinct()
    contratos = Contrato.objects.select_related("oficina").order_by("numero")
    oficinas = OficinaRegional.objects.all().order_by("nombre")

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
        for key in data.keys():
            data[key] = (request.POST.get(key) or "").strip()

        errors = []
        if not data["siged"]:
            errors.append("El N.º SIGED es obligatorio.")
        if not data["carta_linea"]:
            errors.append("La carta de línea es obligatoria.")
        if not data["razon_social"]:
            errors.append("La razón social es obligatoria.")

        supervisor_obj = supervisors.filter(id=data["supervisor_id"]).first() if data["supervisor_id"] else None

        fecha_asignacion = None
        if data["fecha_asignacion"]:
            try:
                fecha_asignacion = datetime.date.fromisoformat(data["fecha_asignacion"])
            except ValueError:
                errors.append("La fecha de asignación no tiene un formato válido (AAAA-MM-DD).")
        else:
            errors.append("Debes seleccionar una fecha de asignación.")

        if not errors:
            expediente = Expediente.objects.create(
                contrato_id=data["contrato"] or None,
                siged=data["siged"],
                carta_linea=data["carta_linea"],
                codigo=data["codigo"] or None,
                codigo_actividad=data["codigo_actividad"] or None,
                razon_social=data["razon_social"],
                tipo_supervision=data["tipo_supervision"] or None,
                tipo_documento=data["tipo_documento"] or None,
                oficina_id=data["oficina"] or None,
                supervisor=supervisor_obj,
                visita_decision=data["visita_decision"],
                fecha_asignacion=fecha_asignacion,
                estado="EN_PROCESO",
            )

            # 🔹 Crear anuncio automático para el supervisor asignado
            if supervisor_obj and supervisor_obj.user:
                Anuncio.objects.create(
                    titulo=f"Nuevo expediente asignado: {expediente.siged}",
                    contenido=(
                        f"El coordinador {request.user.get_full_name()} te ha asignado el expediente "
                        f"N° {expediente.siged} ({expediente.carta_linea}).\n\n"
                        f"**Razón social:** {expediente.razon_social}\n"
                        f"**Tipo de supervisión:** {expediente.tipo_supervision or 'No especificado'}\n"
                        f"**Fecha de asignación:** {expediente.fecha_asignacion.strftime('%d/%m/%Y')}"
                    ),
                    tipo="asignacion",
                    destinatario=supervisor_obj.user,
                    remitente=request.user,
                )

            messages.success(request, "✅ Expediente registrado correctamente y anuncio enviado al supervisor.")
            return redirect("asignaciones:coordinador_registrar")

        for e in errors:
            messages.error(request, e)

    context = {
        "supervisores": supervisors,
        "oficinas": oficinas,
        "contratos": contratos,
        "data": data,
    }
    return render(request, "coordinador/registrar.html", context)


def coordinador_revisar(request):
    qs = Expediente.objects.select_related("supervisor", "contrato", "oficina").order_by("-created_at")
    contrato_id = request.GET.get("contrato")
    siged = request.GET.get("siged", "").strip()
    if contrato_id:
        qs = qs.filter(contrato_id=contrato_id)
    if siged:
        qs = qs.filter(siged__icontains=siged)

    contratos = Contrato.objects.select_related("oficina").order_by("numero")
    return render(request, "coordinador/revisar.html", {"expedientes": qs, "contratos": contratos})


# ============================================================
#                         Admin / Paneles
# ============================================================

def admin_general_menu(request):
    return render(request, "admin/menu_general.html")


def admin_simple_menu(request):
    return render(request, "admin/menu_simple.html")


def admin_general_descargar(request):
    return render(request, "admin/descargar_general.html")


def admin_simple_descargar(request):
    return render(request, "admin/descargar_simple.html")

def admin_general_revisar(request):
    contratos = Contrato.objects.all().order_by("numero")
    expedientes = []

    contrato_id = request.GET.get("contrato")
    siged = request.GET.get("siged", "").strip()
    carta_linea = request.GET.get("carta_linea", "").strip()

    if contrato_id or siged or carta_linea:
        qs = Expediente.objects.select_related("contrato", "oficina", "supervisor")
        if contrato_id:
            qs = qs.filter(contrato_id=contrato_id)
        if siged:
            qs = qs.filter(siged__icontains=siged)
        if carta_linea:
            qs = qs.filter(carta_linea__icontains=carta_linea)

        expedientes = qs.order_by("-fecha_asignacion")
        if not expedientes:
            messages.info(request, "No se encontraron expedientes con los filtros aplicados.")

    context = {
        "contratos": contratos,
        "expedientes": expedientes,
    }
    return render(request, "admin/revisar_general.html", context)


def admin_simple_revisar(request):
    contratos = Contrato.objects.all().order_by("numero")
    expedientes = []

    contrato_id = request.GET.get("contrato")
    siged = request.GET.get("siged", "").strip()
    carta_linea = request.GET.get("carta_linea", "").strip()

    if contrato_id or siged or carta_linea:
        qs = Expediente.objects.select_related("contrato", "oficina", "supervisor")
        if contrato_id:
            qs = qs.filter(contrato_id=contrato_id)
        if siged:
            qs = qs.filter(siged__icontains=siged)
        if carta_linea:
            qs = qs.filter(carta_linea__icontains=carta_linea)

        expedientes = qs.order_by("-fecha_asignacion")
        if not expedientes:
            messages.info(request, "No se encontraron expedientes con los filtros aplicados.")

    context = {
        "contratos": contratos,
        "expedientes": expedientes,
    }
    return render(request, "admin/revisar_simple.html", context)

from django.contrib.auth.models import Group, User
from .forms import CrearUsuarioForm
from django.contrib import messages
from django.shortcuts import render, redirect

def crear_usuario(request):
    """
    Permite crear nuevos usuarios y asignarles un rol (grupo).
    Temporalmente sin restricción de login.
    """
    if request.method == "POST":
        form = CrearUsuarioForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password"])
            user.save()

            grupo = form.cleaned_data["grupo"]
            user.groups.add(grupo)

            messages.success(request, f"✅ Usuario '{user.username}' creado con rol '{grupo.name}'.")
            return redirect("crear_usuario")
    else:
        form = CrearUsuarioForm()

    usuarios = User.objects.all().order_by("username")
    return render(request, "usuarios/crear.html", {"form": form, "usuarios": usuarios})


# ============================================================
#                  BANDEJA DE ENTRADA (MENSAJES)
# ============================================================

def bandeja(request):
    usuario = getattr(request, 'user', None)
    if not usuario or not getattr(usuario, 'is_authenticated', False):
        class DummyUser:
            id = 0
            username = "Invitado"
            is_authenticated = False
        usuario = DummyUser()

    role = user_role(usuario) if usuario.is_authenticated else "INVITADO"

    recibidos = Mensaje.objects.filter(destinatario=usuario).select_related("remitente") if usuario.is_authenticated else Mensaje.objects.all()[:25]

    if request.method == "POST":
        dest_id = request.POST.get("destinatario")
        asunto = request.POST.get("asunto", "").strip()
        cuerpo = request.POST.get("cuerpo", "").strip()

        if not asunto or not cuerpo:
            messages.error(request, "Todos los campos son obligatorios.")
        else:
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

    return render(request, "misc/bandeja.html", {"recibidos": recibidos, "usuarios": usuarios, "role": role})


# ============================================================
#                     ANUNCIOS (MÓDULO MISC)
# ============================================================

from django.contrib.auth.models import Group
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import models
from django.contrib.auth.models import User
from .models import Anuncio


# ------------------------------------------------------------
# Listar anuncios
# ------------------------------------------------------------
def anuncios(request):
    """
    Muestra los anuncios para el usuario actual.
    Si no está autenticado, solo muestra los generales.
    Si es petición AJAX, devuelve el bloque HTML para refresco.
    """
    user = request.user

    # Validar si el usuario puede crear anuncios
    puede_crear = False
    if user.is_authenticated and user.groups.filter(
        name__in=["Coordinador", "Administrador General", "Administrador Simple"]
    ).exists():
        puede_crear = True

    # Mostrar anuncios según el tipo de usuario
    if not user.is_authenticated:
        anuncios = Anuncio.objects.filter(tipo="general").order_by("-fecha_creacion")
    else:
        anuncios = Anuncio.objects.filter(
            models.Q(destinatario=user)
            | models.Q(grupo_destino__in=user.groups.all())
            | models.Q(tipo="general")
        ).select_related("remitente").order_by("-fecha_creacion")

    # Si es llamada AJAX, devuelvo solo la lista renderizada
    if request.GET.get("ajax"):
        html = render_to_string("misc/partials/_anuncios_list.html", {"anuncios": anuncios})
        return HttpResponse(html)

    # Paso la variable `puede_crear` al contexto del template
    return render(
        request,
        "misc/anuncios.html",
        {"anuncios": anuncios, "puede_crear": puede_crear},
    )

# ------------------------------------------------------------
# Crear anuncio (solo coordinadores o administradores)
# ------------------------------------------------------------
def crear_anuncio(request):
    """
    Permite a coordinadores y administradores crear nuevos anuncios
    dirigidos a grupos completos o a usuarios específicos.
    """
    if not request.user.groups.filter(
        name__in=["Coordinador", "Administrador General", "Administrador Simple"]
    ).exists():
        messages.error(request, "No tienes permiso para crear anuncios.")
        return redirect("asignaciones:anuncios")

    grupos = Group.objects.all().order_by("name")
    usuarios = User.objects.all().order_by("first_name", "last_name")

    if request.method == "POST":
        titulo = request.POST.get("titulo", "").strip()
        contenido = request.POST.get("contenido", "").strip()
        tipo = request.POST.get("tipo", "general")
        grupo_id = request.POST.get("grupo_destino")
        destinatario_id = request.POST.get("destinatario")

        if not titulo or not contenido:
            return JsonResponse({"status": "error", "message": "Campos incompletos."})

        anuncio = Anuncio(
            titulo=titulo,
            contenido=contenido,
            tipo=tipo,
            remitente=request.user,
        )

        if grupo_id:
            anuncio.grupo_destino_id = grupo_id
        if destinatario_id:
            anuncio.destinatario_id = destinatario_id

        anuncio.save()
        return JsonResponse({"status": "success"})

    return render(request, "misc/crear_anuncio.html", {"grupos": grupos, "usuarios": usuarios})


# ------------------------------------------------------------
# Crear anuncio global (para generar automáticamente)
# ------------------------------------------------------------
def crear_anuncio_global(tipo, titulo, contenido, remitente, grupo_nombre=None):
    """
    Función utilitaria para generar anuncios globales automáticamente.
    Puede ser llamada desde cualquier vista o evento del sistema.
    """
    grupo = None
    if grupo_nombre:
        grupo = Group.objects.filter(name=grupo_nombre).first()

    Anuncio.objects.create(
        titulo=titulo,
        contenido=contenido,
        tipo=tipo,
        remitente=remitente,
        grupo_destino=grupo,
    )


# ============================================================
#                          REPORTES
# ============================================================

def reportes(request):
    usuario = getattr(request, 'user', None)
    role = user_role(usuario) if usuario and getattr(usuario, 'is_authenticated', False) else "INVITADO"
    return render(request, "misc/reportes.html", {"role": role})

# ============================================================
# Endpoint AJAX con filtrado por supervisor logueado
# ============================================================


def ajax_autocomplete(request):
    """
    Este endpoint devuelve sugerencias en tiempo real para los campos:
      - N° SIGED
      - Carta Línea
    Filtra automáticamente los expedientes del supervisor logueado (si aplica).
    """

    field = request.GET.get("field", "").strip()
    query = request.GET.get("q", "").strip()

    if not field or not query:
        return JsonResponse({"results": []})

    # Obtengo el supervisor actual si está autenticado
    supervisor = getattr(request.user, "supervisor", None)

    # Base de expedientes
    expedientes = Expediente.objects.all()

    # 🔒 Si el usuario logueado tiene rol de supervisor, filtro solo los suyos
    if supervisor:
        expedientes = expedientes.filter(supervisor=supervisor)

    # Filtro dinámico según el campo
    if field == "siged":
        resultados = (
            expedientes.filter(siged__icontains=query)
            .values_list("siged", flat=True)
            .distinct()[:10]
        )
    elif field == "carta_linea":
        resultados = (
            expedientes.filter(carta_linea__icontains=query)
            .values_list("carta_linea", flat=True)
            .distinct()[:10]
        )
    else:
        resultados = []

    return JsonResponse({"results": list(resultados)})
# ============================================================
# AJAX: Registrar fecha de visita
# ============================================================
from django.views.decorators.http import require_POST

@require_POST
def ajax_registrar_visita(request):
    """
    Registra o actualiza la fecha de visita de un expediente mediante AJAX.
    Esta ruta se usa desde registrar.html sin recargar la página.
    """
    siged = request.POST.get("siged", "").strip()
    carta = request.POST.get("carta_linea", "").strip()
    fecha_visita = request.POST.get("fecha_visita", "").strip()

    if not siged and not carta:
        return JsonResponse({"status": "error", "message": "Debe ingresar N° SIGED o Carta Línea."})
    if not fecha_visita:
        return JsonResponse({"status": "error", "message": "Debe ingresar una fecha válida."})

    # Busco el expediente correspondiente
    exp = Expediente.objects.filter(
        Q(siged__iexact=siged) | Q(carta_linea__iexact=carta)
    ).first()

    if not exp:
        return JsonResponse({"status": "error", "message": "No se encontró el expediente."})

    exp.fecha_visita = fecha_visita
    exp.estado = "EN_PROCESO"
    exp.save()

    return JsonResponse({
        "status": "success",
        "message": f"Fecha de visita registrada correctamente para el expediente {exp.siged}.",
        "siged": exp.siged,
        "carta_linea": exp.carta_linea,
        "fecha_visita": exp.fecha_visita.strftime("%d/%m/%Y"),
        "razon_social": exp.razon_social or "—",
    })
# ============================================================
# AJAX: Actualizar estado de expediente
# ============================================================
@require_POST
def ajax_actualizar_estado(request):
    """
    Permite al supervisor actualizar el estado del expediente vía AJAX.
    Valida que se haya marcado el toggle 'Concluido' y una fecha válida.
    """
    siged = request.POST.get("siged", "").strip()
    carta = request.POST.get("carta_linea", "").strip()
    fecha_derivacion = request.POST.get("fecha_derivacion", "").strip()
    observaciones = request.POST.get("observaciones", "").strip()
    estado = request.POST.get("estado", "").strip()

    if not siged and not carta:
        return JsonResponse({"status": "error", "message": "Debe ingresar N° SIGED o Carta Línea."})
    if not fecha_derivacion:
        return JsonResponse({"status": "error", "message": "Debe ingresar la fecha de derivación."})
    if estado != "CONCLUIDO":
        return JsonResponse({"status": "error", "message": "Solo se puede guardar si se marca como concluido."})

    exp = Expediente.objects.filter(
        Q(siged__iexact=siged) | Q(carta_linea__iexact=carta)
    ).first()

    if not exp:
        return JsonResponse({"status": "error", "message": "Expediente no encontrado."})

    exp.fecha_derivacion = fecha_derivacion
    exp.observaciones = observaciones or "-"
    exp.estado = "CONCLUIDO"
    exp.save()

    return JsonResponse({
        "status": "success",
        "message": f"Expediente {exp.siged} actualizado como concluido.",
        "siged": exp.siged,
        "fecha_derivacion": exp.fecha_derivacion.strftime("%d/%m/%Y"),
        "estado": exp.estado,
        "observaciones": exp.observaciones,
    })

from django.shortcuts import render, redirect
from django.contrib.auth.models import User, Group
from django.contrib import messages
from .forms import UsuarioForm

def crear_usuario(request):
    """
    Permite crear nuevos usuarios y asignarles un rol (grupo).
    Temporalmente sin requerir autenticación (sin @login_required).
    """
    if request.method == 'POST':
        form = UsuarioForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            password = form.cleaned_data['password']
            group = form.cleaned_data['group']
            user.set_password(password)
            user.save()
            user.groups.add(group)

            messages.success(request, f"✅ Usuario '{user.username}' creado con rol '{group.name}'.")
            return redirect('asignaciones:admin_general_menu')  # Redirección corregida
        else:
            messages.error(request, "❌ Error al crear el usuario. Verifica los datos ingresados.")
    else:
        form = UsuarioForm()

    return render(request, 'asignaciones/crear_usuario.html', {'form': form})

from django.contrib.auth.models import User, Group
from django.shortcuts import render

def lista_usuarios(request):
    usuarios = User.objects.all().order_by('id')
    usuarios_data = []

    for u in usuarios:
        grupo = u.groups.first().name if u.groups.exists() else "Sin rol"
        usuarios_data.append({
            'id': u.id,
            'username': u.username,
            'first_name': u.first_name,
            'last_name': u.last_name,
            'email': u.email,
            'group': grupo
        })

    context = {'usuarios': usuarios_data}
    return render(request, 'asignaciones/lista_usuarios.html', context)


from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages

def eliminar_usuario(request, user_id):
    usuario = get_object_or_404(User, id=user_id)

    if usuario.username.lower() == "admin" or usuario.is_superuser:
        messages.error(request, "⚠️ No se puede eliminar al usuario administrador principal.")
        return redirect('asignaciones:lista_usuarios')

    usuario.delete()
    messages.success(request, f"✅ Usuario '{usuario.username}' eliminado correctamente.")
    return redirect('asignaciones:lista_usuarios')


def editar_usuario(request, user_id):
    usuario = get_object_or_404(User, id=user_id)
    grupos = Group.objects.all()  # lista de roles

    if request.method == "POST":
        usuario.first_name = request.POST.get("first_name")
        usuario.last_name = request.POST.get("last_name")
        usuario.email = request.POST.get("email")

        nuevo_rol = request.POST.get("rol")
        if nuevo_rol:
            usuario.groups.clear()
            grupo = Group.objects.get(name=nuevo_rol)
            usuario.groups.add(grupo)

        usuario.save()
        messages.success(request, f"✅ Usuario '{usuario.username}' actualizado correctamente.")
        return redirect("asignaciones:lista_usuarios")

    rol_actual = usuario.groups.first().name if usuario.groups.exists() else "Sin rol"

    context = {
        "usuario": usuario,
        "grupos": grupos,
        "rol_actual": rol_actual,
    }
    return render(request, "asignaciones/editar_usuario.html", context)



