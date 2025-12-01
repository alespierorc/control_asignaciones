# ============================================================
#                CONTROL DE ASIGNACIONES - SERMINCO
# ============================================================
# Archivo: views.py
# Propósito: Control de vistas, seguridad por roles y lógica de negocio.
# Roles soportados: AdministradorLider, Administrador, Coordinador, Supervisor
# ============================================================

from django.db.models import Q
from django.urls import reverse
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User, Group
from django.views.decorators.http import require_POST
import datetime
from django.views.decorators.csrf import csrf_protect
from .models import Expediente, Contrato, OficinaRegional, Mensaje, Anuncio
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages

from .forms import (
    ProgramarVisitaForm,
    ConcluirForm,
    CoordinadorRegistroForm,
    CrearUsuarioForm,
)

# ============================================================
#                       FUNCIONES DE ROL
# ============================================================

def has_group(user, group_name):
    """Verifica si el usuario pertenece a un grupo específico."""
    return user.is_authenticated and user.groups.filter(name=group_name).exists()


def user_role(user):
    """Devuelve el rol principal del usuario."""
    if user.is_superuser or has_group(user, "AdministradorLider"):
        return "ADMIN_LIDER"
    if has_group(user, "Administrador"):
        return "ADMIN"
    if has_group(user, "Coordinador"):
        return "COORD"
    if has_group(user, "Supervisor"):
        return "SUP"
    return None


def role_required(groups):
    """Decorador que restringe el acceso según el grupo."""
    def decorator(view_func):
        @login_required
        def wrapper(request, *args, **kwargs):
            user = request.user
            if user.is_superuser or has_group(user, "AdministradorLider"):
                return view_func(request, *args, **kwargs)
            if any(has_group(user, g) for g in groups):
                return view_func(request, *args, **kwargs)
            messages.error(request, "⚠️ No tienes permisos para acceder a esta sección.")
            return redirect("asignaciones:home_router")
        return wrapper
    return decorator

# ============================================================
# AUTENTICACIÓN Y REDIRECCIÓN POR ROL
# ============================================================

@csrf_protect
def login_demo(request):
    """Inicio de sesión personalizado SERMINCO."""
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f"👋 Bienvenido, {user.first_name or user.username}.")
            return redirect("asignaciones:home_router")
        else:
            messages.error(request, "❌ Usuario o contraseña incorrectos.")
            return redirect("asignaciones:login")

    if request.user.is_authenticated:
        return redirect("asignaciones:home_router")

    return render(request, "registration/login.html")

@login_required
def home_router(request):
    """Redirige al panel correspondiente según el rol del usuario."""
    user = request.user

    role = user_role(user)
    if role == "ADMIN_LIDER":
        return redirect("asignaciones:admin_lider_menu")
    elif role == "ADMIN":
        return redirect("asignaciones:admin_menu")
    elif role == "COORD":
        return redirect("asignaciones:coordinador_menu")
    elif role == "SUP":
        return redirect("asignaciones:supervisor_panel")
    else:
        messages.warning(request, "Tu cuenta no tiene un rol asignado. Contacta con el AdministradorLider.")
        logout(request)
        return redirect("asignaciones:login")


@csrf_protect
@login_required
def logout_view(request):
    """
    Cierra completamente la sesión del usuario y limpia las cookies.
    """
    try:
        logout(request)  # Cierra la sesión en Django
        request.session.flush()  # Elimina los datos de sesión
        response = redirect("asignaciones:login")
        response.delete_cookie("sessionid")
        response.delete_cookie("csrftoken")
        messages.success(request, "👋 Has cerrado sesión correctamente.")
        return response
    except Exception as e:
        print(f"⚠️ Error al cerrar sesión: {e}")
        messages.error(request, "⚠️ No se pudo cerrar sesión correctamente.")
        return redirect("asignaciones:home_router")

# ============================================================
#                        SUPERVISOR
# ============================================================
from django.contrib.auth.decorators import login_required, user_passes_test

@login_required
@user_passes_test(lambda u: u.groups.filter(name__in=["Supervisor", "AdministradorLider"]).exists())
def supervisor_panel(request):
    """
    Panel principal del Supervisor.
    - Solo los usuarios con rol 'Supervisor' o 'AdministradorLider' pueden acceder.
    - El AdministradorLider tiene control total sobre este panel también.
    """
    return render(request, "roles/supervisor_home.html")

@role_required(["Supervisor"])
def home_supervisor(request):
    return render(request, "roles/supervisor_home.html")

# ============================================================
#            REGISTRO DE VISITA POR SUPERVISOR
# ============================================================
from datetime import datetime
from django.http import JsonResponse
from django.shortcuts import render
from django.contrib import messages
from .models import Expediente, Anuncio
from .decorators import role_required
from django.contrib.auth.models import User


@role_required(["Supervisor"])
def supervisor_registrar(request):
    """
    Permite al supervisor registrar la fecha de visita de un expediente.
    Retorna JSON si la solicitud es AJAX, o renderiza la vista normal.
    """
    supervisor = request.user
    expedientes = Expediente.objects.filter(supervisor=supervisor).select_related("contrato", "oficina")

    # === Si el usuario envía el formulario vía AJAX ===
    if request.method == "POST" and request.headers.get("X-Requested-With") == "XMLHttpRequest":
        try:
            expediente_id = request.POST.get("expediente_id")
            fecha_visita_str = request.POST.get("fecha_visita")

            if not expediente_id or not fecha_visita_str:
                return JsonResponse({"status": "error", "message": "Datos incompletos"})

            # ✅ Convertir la fecha desde string a objeto date
            try:
                fecha_visita = datetime.strptime(fecha_visita_str, "%Y-%m-%d").date()
            except ValueError:
                return JsonResponse({"status": "error", "message": "Formato de fecha inválido"})

            expediente = Expediente.objects.filter(id=expediente_id, supervisor=supervisor).first()
            if not expediente:
                return JsonResponse({"status": "error", "message": "Expediente no encontrado o no asignado"})

            # ✅ Guardar la fecha de visita y actualizar estado
            expediente.fecha_visita = fecha_visita
            expediente.estado = "CONCLUIDO"
            expediente.save()

            # ✅ Crear anuncio para el Coordinador
            coordinadores = User.objects.filter(groups__name="Coordinador")
            for coord in coordinadores:
                Anuncio.objects.create(
                    titulo=f"Visita registrada - {expediente.siged}",
                    contenido=f"El supervisor {supervisor.get_full_name()} registró la visita el {fecha_visita.strftime('%d/%m/%Y')}",
                    tipo="INFO",
                    remitente=supervisor,
                    destinatario=coord,
                )

            return JsonResponse({
                "status": "success",
                "message": "Visita registrada correctamente",
                "fecha_visita": fecha_visita.strftime("%d/%m/%Y"),
            })

        except Exception as e:
            print(f"❌ Error al guardar visita: {e}")
            return JsonResponse({"status": "error", "message": str(e)})

    # === Renderizado normal (GET) ===
    return render(request, "supervisor/registrar.html", {"expedientes": expedientes})

@role_required(["Supervisor", "AdministradorLider"])
def estado_expediente(request):
    """
    Vista para gestión de estado de expedientes:
    - GET AJAX: búsqueda de expedientes por SIGED o carta de línea
    - POST AJAX: actualización de estado, fecha derivación y observaciones
    """
    # ==== BÚSQUEDA (AJAX GET) ====
    if request.headers.get("x-requested-with") == "XMLHttpRequest" and request.method == "GET":
        siged = request.GET.get("siged", "").strip()
        carta = request.GET.get("carta_linea", "").strip()
        query = siged or carta
        if not query:
            return JsonResponse({"status": "error", "message": "Sin parámetros de búsqueda.", "results": []})

        expedientes = Expediente.objects.all()
        if request.user.groups.filter(name="Supervisor").exists():
            expedientes = expedientes.filter(supervisor=request.user)

        filtro = Q()
        if siged:
            filtro |= Q(siged__icontains=siged)
        if carta:
            filtro |= Q(carta_linea__icontains=carta)

        expedientes = expedientes.filter(filtro).select_related(
            "contrato", "oficina", "tipo_supervision"
        )[:20]

        resultados = [
            {
                "id": e.id,
                "siged": e.siged,
                "carta_linea": e.carta_linea or "",
                "razon_social": e.razon_social or "",
                "contrato": e.contrato.numero if e.contrato else "",
                "oficina": e.oficina.nombre if e.oficina else "",
                "codigo_actividad": e.codigo_actividad or "",
                "tipo_supervision": e.tipo_supervision.nombre if e.tipo_supervision else "—",
                "fecha_asignacion": e.fecha_asignacion.strftime("%d/%m/%Y") if e.fecha_asignacion else "—",
                "estado": e.estado or "EN PROCESO",
                "fecha_derivacion": e.fecha_derivacion.strftime("%d/%m/%Y") if e.fecha_derivacion else "—",
                "observaciones": e.observaciones or "—",
            }
            for e in expedientes
        ]

        return JsonResponse({"status": "success", "results": resultados})

    # ==== ACTUALIZACIÓN (AJAX POST) ====
    if request.headers.get("x-requested-with") == "XMLHttpRequest" and request.method == "POST":
        try:
            exp_id = request.POST.get("expediente", "").strip()
            fecha_deriv = request.POST.get("fecha_derivacion", "").strip()
            observaciones = request.POST.get("observaciones", "").strip()
            estado = request.POST.get("estado", "").strip()

            if not exp_id:
                return JsonResponse({"status": "error", "message": "No se identificó el expediente."})
            if not fecha_deriv:
                return JsonResponse({"status": "error", "message": "Debe ingresar la fecha de derivación."})

            exp = Expediente.objects.filter(id=exp_id).first()
            if request.user.groups.filter(name="Supervisor").exists():
                exp = Expediente.objects.filter(id=exp.id, supervisor=request.user).first()

            if not exp:
                return JsonResponse({"status": "error", "message": "Expediente no encontrado o no asignado."})

            # Convertir string a date
            try:
                fecha_convertida = datetime.strptime(fecha_deriv, "%Y-%m-%d").date()
            except ValueError:
                return JsonResponse({"status": "error", "message": "Formato de fecha no válido."})

            exp.fecha_derivacion = fecha_convertida
            exp.observaciones = observaciones or "-"
            exp.estado = "CONCLUIDO" if estado == "CONCLUIDO" else "EN PROCESO"
            exp.save()

            return JsonResponse({
                "status": "success",
                "message": "Expediente actualizado correctamente.",
                "expediente": {
                    "id": exp.id,
                    "siged": exp.siged,
                    "estado": exp.estado,
                    "fecha_derivacion": exp.fecha_derivacion.strftime("%d/%m/%Y"),
                    "observaciones": exp.observaciones,
                }
            })
        except Exception as e:
            print("❌ Error en estado_expediente:", e)
            return JsonResponse({"status": "error", "message": f"Error interno: {e}"})

    # ==== RENDER NORMAL ====
    expedientes = Expediente.objects.filter(supervisor=request.user).select_related(
        "contrato", "oficina", "tipo_supervision", "tipo_documento"
    )
    return render(request, "supervisor/estado.html", {"expedientes": expedientes})

# ============================================================
#                         COORDINADOR
# ============================================================

@role_required(["Coordinador"])
def coordinador_menu(request):
    return render(request, "coordinador/menu.html")

# ============================================================
#          VISTA: REGISTRAR EXPEDIENTE (COORDINADOR)
# ============================================================

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from .models import (
    Expediente,
    OficinaRegional,
    Contrato,
    TipoSupervision,
    TipoDocumento,
    Anuncio,
)
from django.db import transaction
from asignaciones.decorators import role_required


@role_required(["Coordinador"])
@transaction.atomic
def coordinador_registrar(request):
    """
    Permite al coordinador registrar un nuevo expediente.
    Incluye selección de contrato, oficina, tipo de supervisión y documento.
    """

    # Cargar datos base para los selects
    supervisores = User.objects.filter(groups__name="Supervisor").order_by("first_name")
    contratos = Contrato.objects.all().order_by("numero")
    oficinas = OficinaRegional.objects.all().order_by("nombre")
    tipos_supervision = TipoSupervision.objects.all().order_by("nombre")
    tipos_documento = TipoDocumento.objects.all().order_by("nombre")

    data = {}

    if request.method == "POST":
        # Obtener datos del formulario
        data = {k: request.POST.get(k, "").strip() for k in request.POST.keys()}

        # Validar campos obligatorios mínimos
        campos_obligatorios = ["siged", "carta_linea", "contrato", "oficina", "supervisor_id"]
        faltantes = [c for c in campos_obligatorios if not data.get(c)]

        if faltantes:
            messages.error(request, f"⚠️ Debes completar los campos obligatorios: {', '.join(faltantes)}.")
            return render(request, "coordinador/registrar.html", {
                "data": data,
                "supervisores": supervisores,
                "contratos": contratos,
                "oficinas": oficinas,
                "tipos_supervision_choices": [(t.id, t.nombre) for t in tipos_supervision],
                "tipos_documento_choices": [(t.id, t.nombre) for t in tipos_documento],
            })

        try:
            # Convertir IDs en objetos
            contrato = Contrato.objects.get(id=data["contrato"])
            oficina = OficinaRegional.objects.get(id=data["oficina"])
            supervisor = User.objects.get(id=data["supervisor_id"])

            tipo_supervision = (
                TipoSupervision.objects.get(id=data["tipo_supervision"])
                if data.get("tipo_supervision") else None
            )
            tipo_documento = (
                TipoDocumento.objects.get(id=data["tipo_documento"])
                if data.get("tipo_documento") else None
            )

            # Crear expediente
            expediente = Expediente.objects.create(
                siged=data["siged"],
                carta_linea=data["carta_linea"],
                codigo=data.get("codigo", ""),
                codigo_actividad=data.get("codigo_actividad", ""),
                razon_social=data.get("razon_social", ""),
                visita_decision=data.get("visita_decision", "NO"),
                fecha_asignacion=data.get("fecha_asignacion") or None,
                contrato=contrato,
                oficina=oficina,
                supervisor=supervisor,
                tipo_supervision=tipo_supervision,
                tipo_documento=tipo_documento,
                estado="EN_PROCESO",
            )

            # Crear anuncio para el supervisor
            Anuncio.objects.create(
                titulo=f"Nuevo expediente asignado: {expediente.siged}",
                contenido=f"Has recibido un nuevo expediente asignado por {request.user.get_full_name()}.",
                tipo="INFO",
                destinatario=supervisor,
                remitente=request.user,
            )

            messages.success(request, f"✅ Expediente {expediente.siged} registrado correctamente.")
            return redirect("asignaciones:coordinador_registrar")

        except Exception as e:
            messages.error(request, f"❌ Error al guardar el expediente: {e}")

    # Render inicial o reintento fallido
    return render(request, "coordinador/registrar.html", {
        "data": data,
        "supervisores": supervisores,
        "contratos": contratos,
        "oficinas": oficinas,
        "tipos_supervision_choices": [(t.id, t.nombre) for t in tipos_supervision],
        "tipos_documento_choices": [(t.id, t.nombre) for t in tipos_documento],
    })



@role_required(["Coordinador"])
def coordinador_revisar(request):
    qs = Expediente.objects.select_related("supervisor", "contrato", "oficina").order_by("-created_at")
    siged = request.GET.get("siged", "").strip()
    if siged:
        qs = qs.filter(siged__icontains=siged)
    return render(request, "coordinador/revisar.html", {"expedientes": qs})

# ============================================================
#                      ADMINISTRADORES
# ============================================================
# Roles:
# - AdministradorLíder → Control total
# - Administrador → Panel simple
# ============================================================

from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render
from .models import Contrato, Expediente

# ============================================================
# UTILIDAD: VALIDADORES DE ROL
# ============================================================

def es_admin_lider(user):
    """Valida si el usuario pertenece al grupo 'AdministradorLider'."""
    return user.is_authenticated and user.groups.filter(name="AdministradorLider").exists()

def es_admin(user):
    """Valida si el usuario pertenece al grupo 'Administrador'."""
    return user.is_authenticated and user.groups.filter(name="Administrador").exists()

# ============================================================
# ADMINISTRADOR LÍDER (control total del sistema)
# ============================================================

@login_required
@user_passes_test(es_admin_lider)
def admin_lider_menu(request):
    """
    Panel principal del AdministradorLíder.
    Tiene acceso completo a todos los paneles (coordinador, supervisor, etc.)
    y puede crear usuarios, revisar y descargar expedientes.
    """
    return render(request, "admin/admin_lider_menu.html")


@login_required
@user_passes_test(es_admin_lider)
def admin_lider_revisar(request):
    """
    Permite revisar expedientes asignados o totales.
    El AdministradorLíder puede filtrar por SIGED o Contrato.
    """
    siged = request.GET.get("siged", "").strip()
    contratos = Contrato.objects.all().order_by("numero")
    expedientes = Expediente.objects.all().order_by("-fecha_asignacion")

    if siged:
        expedientes = expedientes.filter(siged__icontains=siged)

    context = {
        "siged": siged,
        "contratos": contratos,
        "expedientes": expedientes,
    }
    return render(request, "admin/admin_lider_revisar.html", context)


@login_required
@user_passes_test(es_admin_lider)
def admin_lider_descargar(request):
    """
    Vista del AdministradorLíder para descargar informes, reportes o expedientes.
    """
    contratos = Contrato.objects.all().order_by("numero")
    expedientes = Expediente.objects.all().order_by("-fecha_asignacion")

    context = {
        "contratos": contratos,
        "expedientes": expedientes,
    }
    return render(request, "admin/admin_lider_descargar.html", context)


# ============================================================
# ADMINISTRADOR (nivel intermedio, acceso restringido)
# ============================================================

@login_required
@user_passes_test(es_admin)
def admin_menu(request):
    """
    Panel principal del Administrador.
    Puede revisar y descargar expedientes propios o asignados,
    pero no puede crear usuarios ni acceder a paneles de otros roles.
    """
    return render(request, "admin/admin_menu.html")


@login_required
@user_passes_test(es_admin)
def admin_revisar(request):
    """
    Vista de revisión simple de expedientes.
    """
    siged = request.GET.get("siged", "").strip()
    contratos = Contrato.objects.all().order_by("numero")
    expedientes = Expediente.objects.all().order_by("-fecha_asignacion")

    if siged:
        expedientes = expedientes.filter(siged__icontains=siged)

    context = {
        "siged": siged,
        "contratos": contratos,
        "expedientes": expedientes,
    }
    return render(request, "admin/admin_revisar.html", context)


@login_required
@user_passes_test(es_admin)
def admin_descargar(request):
    """
    Permite descargar listados o reportes.
    """
    contratos = Contrato.objects.all().order_by("numero")
    expedientes = Expediente.objects.all().order_by("-fecha_asignacion")

    context = {
        "contratos": contratos,
        "expedientes": expedientes,
    }
    return render(request, "admin/admin_descargar.html", context)


# ============================================================
#                        GESTIÓN DE USUARIOS
# ============================================================

@role_required(["AdministradorLider"])
def crear_usuario(request):
    """
    Solo el AdministradorLider puede crear cuentas.
    Crea usuarios, les asigna rol y muestra errores claros si algo falla.
    """
    if request.method == "POST":
        form = CrearUsuarioForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"✅ Usuario '{user.username}' creado correctamente.")
            return redirect("asignaciones:lista_usuarios")
        else:
            # Muestra los errores de validación directamente en consola y en el formulario
            print("❌ Errores al crear usuario:", form.errors)
            messages.error(request, "⚠️ Revisa los campos marcados. No se pudo crear el usuario.")
    else:
        form = CrearUsuarioForm()

    return render(request, "usuarios/crear.html", {"form": form})


@role_required(["AdministradorLider"])
def lista_usuarios(request):
    usuarios = User.objects.all().order_by("id")
    usuarios_data = [
        {
            "id": u.id,
            "username": u.username,
            "first_name": u.first_name,
            "last_name": u.last_name,
            "email": u.email,
            "group": u.groups.first().name if u.groups.exists() else "Sin rol",
        }
        for u in usuarios
    ]
    return render(request, "asignaciones/lista_usuarios.html", {"usuarios": usuarios_data})

@role_required(["AdministradorLider"])
def eliminar_usuario(request, user_id):
    usuario = get_object_or_404(User, id=user_id)
    if usuario.is_superuser or usuario.username.lower() == "admin":
        messages.error(request, "⚠️ No se puede eliminar al administrador principal.")
    else:
        usuario.delete()
        messages.success(request, f"✅ Usuario '{usuario.username}' eliminado correctamente.")
    return redirect("asignaciones:lista_usuarios")

# ============================================================
#        ADMINISTRADOR LÍDER - EDITAR USUARIO
# ============================================================

from django.contrib.auth.models import User, Group
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import CrearUsuarioForm as UsuarioForm

@role_required(["AdministradorLider"])
def editar_usuario(request, user_id):
    """
    Permite al AdministradorLíder editar un usuario existente.
    """
    usuario = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        form = UsuarioForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, f"Usuario '{usuario.username}' actualizado correctamente.")
            return redirect("asignaciones:lista_usuarios")
    else:
        form = UsuarioForm(instance=usuario)

    return render(request, "usuarios/editar_usuario.html", {"form": form, "usuario": usuario})


# ============================================================
#                       BANDEJA 
# ============================================================

@login_required
def bandeja(request):
    """Todos los usuarios autenticados pueden acceder."""
    recibidos = Mensaje.objects.filter(destinatario=request.user).select_related("remitente")
    usuarios = User.objects.all()
    return render(request, "misc/bandeja.html", {"recibidos": recibidos, "usuarios": usuarios})

# ============================================================
#                  ANUNCIOS - CREACIÓN Y LISTADO
# ============================================================

from django.contrib.auth.models import Group, User
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Anuncio
from django.db import models

@login_required
def anuncios(request):
    """
    Muestra los anuncios visibles para el usuario actual.
    - Los Coordinadores, Administradores y AdministradorLider pueden crear anuncios.
    - Los Supervisores solo pueden leer.
    """
    user = request.user

    # Validar permisos de creación
    puede_crear = False
    if user.is_authenticated and user.groups.filter(
        name__in=["AdministradorLider", "Administrador", "Coordinador"]
    ).exists():
        puede_crear = True

    # Mostrar anuncios relevantes
    if not user.is_authenticated:
        anuncios = Anuncio.objects.filter(tipo="general").order_by("-fecha_creacion")
    else:
        anuncios = Anuncio.objects.filter(
            models.Q(destinatario=user)
            | models.Q(grupo_destino__in=user.groups.all())
            | models.Q(tipo="general")
        ).select_related("remitente").order_by("-fecha_creacion")

    if request.GET.get("ajax"):
        html = render_to_string("misc/partials/_anuncios_list.html", {"anuncios": anuncios})
        return HttpResponse(html)

    return render(
        request,
        "misc/anuncios.html",
        {"anuncios": anuncios, "puede_crear": puede_crear},
    )


@login_required
def crear_anuncio(request):
    """
    Permite a los AdministradoresLider, Administradores y Coordinadores crear anuncios.
    Los Supervisores no pueden crear.
    """
    if not request.user.groups.filter(
        name__in=["AdministradorLider", "Administrador", "Coordinador"]
    ).exists():
        messages.error(request, "❌ No tienes permiso para crear anuncios.")
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
            messages.error(request, "Todos los campos son obligatorios.")
            return redirect("asignaciones:crear_anuncio")

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
        messages.success(request, f"✅ Anuncio '{titulo}' creado correctamente.")
        return redirect("asignaciones:anuncios")

    return render(request, "misc/crear_anuncio.html", {"grupos": grupos, "usuarios": usuarios})


# ============================================================
#                       REPORTES
# ============================================================

@login_required
def reportes(request):
    role = user_role(request.user)
    return render(request, "misc/reportes.html", {"role": role})

# ============================================================
#                ENDPOINT AJAX - AUTOCOMPLETADO (MEJORADO)
# ============================================================

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Expediente
from .decorators import role_required


@role_required(["AdministradorLider", "Administrador", "Coordinador", "Supervisor"])
@login_required
def ajax_autocomplete(request):
    """
    Retorna coincidencias para autocompletar campos (SIGED o Carta Línea)
    mostrando solo los expedientes visibles por el usuario actual.
    - Los supervisores solo ven sus expedientes asignados.
    - Los administradores y coordinadores pueden ver todos.
    """
    query = request.GET.get("q", "").strip()
    tipo = request.GET.get("tipo", "").strip()  # puede ser "siged" o "carta_linea"

    if not query or not tipo:
        return JsonResponse({"results": []})

    # Filtrar base según el rol del usuario
    user = request.user
    expedientes = Expediente.objects.all()

    if user.groups.filter(name="Supervisor").exists():
        expedientes = expedientes.filter(supervisor=user)

    # Filtro según el campo de búsqueda
    if tipo == "siged":
        expedientes = expedientes.filter(siged__icontains=query)
    elif tipo == "carta_linea":
        expedientes = expedientes.filter(carta_linea__icontains=query)
    else:
        return JsonResponse({"results": []})

    # Armar lista JSON detallada para la tabla del frontend
    resultados = [
        {
            "id": e.id,
            "siged": e.siged,
            "carta_linea": e.carta_linea,
            "razon_social": e.razon_social or "",
            "contrato": e.contrato.numero if e.contrato else "",
            "oficina": e.oficina.nombre if e.oficina else "",
            "fecha_asignacion": e.fecha_asignacion.strftime("%d/%m/%Y") if e.fecha_asignacion else "",
        }
        for e in expedientes[:10]
    ]

    return JsonResponse({"results": resultados})


# ============================================================
#        ENDPOINT AJAX - REGISTRAR VISITA (Supervisor)
# ============================================================

from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from .models import Expediente

@require_POST
@role_required(["Supervisor", "AdministradorLider"])
def ajax_registrar_visita(request):
    """
    Permite al Supervisor registrar o actualizar la fecha de visita
    desde una llamada AJAX sin recargar la página.
    """
    try:
        expediente_id = request.POST.get("expediente_id")
        fecha_visita = request.POST.get("fecha_visita")

        expediente = get_object_or_404(Expediente, id=expediente_id)
        expediente.fecha_visita = fecha_visita
        expediente.save()

        return JsonResponse({"success": True, "message": "Visita registrada correctamente."})
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)})

# ============================================================
#     ENDPOINT AJAX - ACTUALIZAR ESTADO DE EXPEDIENTE
# ============================================================
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from .models import Expediente

@require_POST
@role_required(["AdministradorLider", "Administrador", "Coordinador", "Supervisor"])
def ajax_actualizar_estado(request):
    """
    Permite actualizar el estado de un expediente vía AJAX.
    Usado por roles con permisos para modificar (Coordinador, Admins, Supervisor).
    """
    try:
        expediente_id = request.POST.get("expediente_id")
        nuevo_estado = request.POST.get("nuevo_estado")

        expediente = get_object_or_404(Expediente, id=expediente_id)
        expediente.estado = nuevo_estado
        expediente.save()

        return JsonResponse({
            "success": True,
            "message": f"El estado del expediente {expediente.siged} fue actualizado a '{nuevo_estado}'."
        })

    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": f"Error al actualizar estado: {str(e)}"
        })


