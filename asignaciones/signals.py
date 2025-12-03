# ============================================================
#                   SIGNALS.PY - SERMINCO
# ============================================================
# Configuración inicial automática:
# - Creación y migración de roles (grupos)
# - Inserción de valores base: oficinas, contratos, tipos de supervisión, tipos de documento
# ============================================================

from django.db.models.signals import post_migrate
from django.contrib.auth.models import Group, User
from django.dispatch import receiver
from .models import OficinaRegional, Contrato, TipoSupervision, TipoDocumento
from django.db import transaction


@receiver(post_migrate)
def crear_y_migrar_roles_y_valores(sender, **kwargs):
    """
    Crea los roles y valores iniciales del sistema SERMINCO
    después de ejecutar 'python manage.py migrate'.
    """
    if sender.name != "asignaciones":
        return

    print("⚙️ Configurando valores iniciales SERMINCO...")

    # === 1️⃣ Roles ===
    roles = ["AdministradorLider", "Administrador", "Coordinador", "Supervisor"]
    for nombre in roles:
        Group.objects.get_or_create(name=nombre)
    print("✅ Roles verificados o creados.")

    # === 2️⃣ Oficinas regionales ===
    oficinas_validas = ["Piura", "Lima", "Arequipa", "Moquegua"]
    OficinaRegional.objects.exclude(nombre__in=oficinas_validas).delete()
    for nombre in oficinas_validas:
        OficinaRegional.objects.get_or_create(nombre=nombre)
    print("🏢 Oficinas regionales ajustadas correctamente.")

    # Oficina base para contratos
    oficina_base = OficinaRegional.objects.filter(nombre="Lima").first()

    # === 3️⃣ Contratos ===
    contratos_validos = ["SUP2500192", "SUP2500203", "SUP2500217", "SUP2500235"]
    Contrato.objects.exclude(numero__in=contratos_validos).delete()
    if oficina_base:
        for numero in contratos_validos:
            Contrato.objects.get_or_create(numero=numero, oficina=oficina_base)
        print("📑 Contratos ajustados correctamente.")
    else:
        print("⚠️ No se encontró la oficina base 'Lima' para los contratos.")

    # === 4️⃣ Tipos de supervisión ===
    tipos_supervision_validos = [
        "Actos Inseguros",
        "Atención de Denuncias",
        "Atención de Solicitud de ITF",
        "Atención de Solicitudes de AVC-AVP",
        "Comprobación de operaciones",
        "Condiciones de seguridad",
        "Condiciones de seguridad con observaciones",
        "Control Metrológico CL especial",
        "Control Volumétrico",
        "Criticidad de Cilindros de GLP",
        "Denuncia - Actos Inseguros",
        "Denuncia - PRICE",
        "Denuncias-Informal",
        "Ejecución/Levantamiento de Med. Seg.",
        "Envasado, Pintado y Canje de cilindros",
        "Etiquetados de cilindros de GLP",
        "Informalidad",
        "PRICE",
        "Por Operaciones",
        "RHO - Inscripción, Modificación",
        "RHO - Modificación de datos, suspensión, cancelación y habilitación",
        "SPIC",
        "Supervisión Operativa de Seguridad de CD y RD de GLP",
        "Supervisión Operativa de Seguridad de LV GLP",
        "Supervisión Operativa de Seguridad de LVGLP",
        "Verificación Póliza",
    ]
    TipoSupervision.objects.exclude(nombre__in=tipos_supervision_validos).delete()
    for nombre in tipos_supervision_validos:
        TipoSupervision.objects.get_or_create(nombre=nombre)
    print("🧭 Tipos de supervisión ajustados correctamente.")

    # === 5️⃣ Tipos de documento ===
    tipos_documento_validos = [
        "Informe de Supervisión",
        "Informe Técnico",
        "Ficha de Registro",
        "Resolución",
    ]
    TipoDocumento.objects.exclude(nombre__in=tipos_documento_validos).delete()
    for nombre in tipos_documento_validos:
        TipoDocumento.objects.get_or_create(nombre=nombre)
    print("📄 Tipos de documento ajustados correctamente.")

    print("✅ Configuración inicial SERMINCO completada.")
