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

    # Evitamos conflictos con apps no relacionadas
    if sender.name != "asignaciones":
        return

    print("⚙️ Verificando configuración inicial de SERMINCO...")

    # ============================================================
    # 1️⃣ CREAR / MIGRAR ROLES (GRUPOS)
    # ============================================================
    roles = ["AdministradorLider", "Administrador", "Coordinador", "Supervisor"]
    for nombre in roles:
        Group.objects.get_or_create(name=nombre)
    print("✅ Roles verificados o creados correctamente.")

    # ============================================================
    # 2️⃣ CREAR OFICINAS REGIONALES
    # ============================================================
    oficinas = [
        "Lima",
        "Arequipa",
        "Cusco",
        "Trujillo",
        "Chiclayo",
        "Piura",
        "Huancayo",
        "Iquitos",
        "Puno",
    ]
    for nombre in oficinas:
        OficinaRegional.objects.get_or_create(nombre=nombre)
    print(f"🏢 Oficinas regionales creadas/verificadas. Oficina base: {oficinas[0]}")

    # Obtenemos la oficina base "Lima" (necesaria para contratos)
    oficina_base = OficinaRegional.objects.filter(nombre="Lima").first()

    # ============================================================
    # 3️⃣ CREAR CONTRATOS (ASOCIADOS A LA OFICINA BASE)
    # ============================================================
    contratos = [
        "SUP2500192",
        "SUP2500275",
        "SUP2500300",
        "SUP2500350",
    ]

    if oficina_base:
        for numero in contratos:
            Contrato.objects.get_or_create(numero=numero, oficina=oficina_base)
        print("📑 Contratos creados/verificados correctamente.")
    else:
        print("⚠️ No se encontró la oficina base 'Lima'. Contratos no creados.")

    # ============================================================
    # 4️⃣ TIPOS DE SUPERVISIÓN
    # ============================================================
    tipos_supervision = [
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

    for nombre in tipos_supervision:
        TipoSupervision.objects.get_or_create(nombre=nombre)
    print("🧭 Tipos de supervisión creados/verificados correctamente.")

    # ============================================================
    # 5️⃣ TIPOS DE DOCUMENTO
    # ============================================================
    tipos_documento = [
        "Oficio múltiple",
        "Ficha de registro de hidrocarburos",
        "Informe técnico",
        "Resolución",
        "Informe de resultados",
        "Comunicación interna",
        "Carta de observaciones",
        "Informe de seguimiento",
        "Informe de auditoría",
        "Acta de verificación",
        "Recomendación técnica",
        "Acta de reunión",
        "Documento de coordinación",
        "Carta de respuesta",
        "Memorando",
        "Otro",
    ]
    for nombre in tipos_documento:
        TipoDocumento.objects.get_or_create(nombre=nombre)
    print("📄 Tipos de documento creados/verificados correctamente.")

    # ============================================================
    # 6️⃣ MIGRAR USUARIOS EXISTENTES A NUEVOS ROLES (si aplica)
    # ============================================================
    try:
        admin_general = Group.objects.get(name="AdministradorLider")
        admin_simple = Group.objects.get(name="Administrador")

        # Usuarios antiguos con roles antiguos
        users_general = User.objects.filter(groups__name="AdminGeneral")
        users_simple = User.objects.filter(groups__name="AdminSimple")

        with transaction.atomic():
            for user in users_general:
                user.groups.clear()
                user.groups.add(admin_general)

            for user in users_simple:
                user.groups.clear()
                user.groups.add(admin_simple)

        if users_general.exists() or users_simple.exists():
            print("🔁 Migración de roles antiguos completada.")
        else:
            print("✅ Roles actualizados, sin migraciones pendientes.")
    except Exception as e:
        print(f"⚠️ Error al migrar usuarios antiguos: {e}")

    print("✅ Configuración inicial completada con éxito.")
