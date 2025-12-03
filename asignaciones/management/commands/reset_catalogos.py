from django.core.management.base import BaseCommand
from django.db import transaction
from asignaciones.models import (
    Contrato, TipoSupervision, TipoDocumento, OficinaRegional, Expediente
)
from django.contrib.auth.models import Group


class Command(BaseCommand):
    help = "Limpia, repuebla y repara los catálogos base de SERMINCO."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("⚙️ Iniciando actualización integral de catálogos SERMINCO...\n"))

        # === Roles base ===
        roles = ["AdministradorLider", "Administrador", "Coordinador", "Supervisor"]
        for nombre in roles:
            Group.objects.get_or_create(name=nombre)
        self.stdout.write(self.style.SUCCESS("👥 Roles verificados o creados."))

        # === 1️⃣ Oficinas ===
        oficinas_validas = ["Piura", "Lima", "Arequipa", "Moquegua"]
        oficina_base, _ = OficinaRegional.objects.get_or_create(nombre="Lima")

        # Reasignar contratos que dependen de oficinas no válidas
        oficinas_invalidas = OficinaRegional.objects.exclude(nombre__in=oficinas_validas)
        if oficinas_invalidas.exists():
            self.stdout.write("🔄 Reasignando contratos con oficinas obsoletas a 'Lima'...")

            for contrato in Contrato.objects.filter(oficina__in=oficinas_invalidas):
                # Si ya existe un contrato con el mismo número en Lima, eliminar el duplicado viejo
                if Contrato.objects.filter(numero=contrato.numero, oficina=oficina_base).exists():
                    self.stdout.write(
                        f"🗑️  Eliminando contrato duplicado {contrato.numero} ({contrato.oficina.nombre})..."
                    )
                    contrato.delete()
                else:
                    contrato.oficina = oficina_base
                    contrato.save(update_fields=["oficina"])

        # Ahora sí se pueden eliminar las oficinas inválidas
        oficinas_invalidas.delete()

        # Crear oficinas válidas
        for nombre in oficinas_validas:
            OficinaRegional.objects.get_or_create(nombre=nombre)
        self.stdout.write(self.style.SUCCESS("🏢 Oficinas regionales actualizadas."))

        # === 2️⃣ Contratos ===
        contratos_validos = ["SUP2500192", "SUP2500203", "SUP2500217", "SUP2500235"]
        Contrato.objects.exclude(numero__in=contratos_validos).delete()
        for numero in contratos_validos:
            Contrato.objects.get_or_create(numero=numero, defaults={"oficina": oficina_base})
        self.stdout.write(self.style.SUCCESS("📑 Contratos actualizados."))

        # === 3️⃣ Tipos de Supervisión ===
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
        self.stdout.write(self.style.SUCCESS("🧭 Tipos de supervisión actualizados."))

        # === 4️⃣ Tipos de Documento ===
        tipos_documento_validos = [
            "Informe de Supervisión",
            "Informe Técnico",
            "Ficha de Registro",
            "Resolución",
        ]
        TipoDocumento.objects.exclude(nombre__in=tipos_documento_validos).delete()
        for nombre in tipos_documento_validos:
            TipoDocumento.objects.get_or_create(nombre=nombre)
        self.stdout.write(self.style.SUCCESS("📄 Tipos de documento actualizados."))

        # === 5️⃣ Reparación de relaciones rotas ===
        self.stdout.write("\n🧩 Verificando referencias rotas en expedientes...")
        contrato_default = Contrato.objects.filter(numero="SUP2500192").first()
        tipo_doc_default = TipoDocumento.objects.filter(nombre="Informe Técnico").first()
        tipo_sup_default = TipoSupervision.objects.filter(nombre="Condiciones de seguridad").first()

        reparados = 0
        for exp in Expediente.objects.all():
            modificado = False
            if exp.contrato is None:
                exp.contrato = contrato_default
                modificado = True
            if exp.oficina is None:
                exp.oficina = oficina_base
                modificado = True
            if exp.tipo_documento is None:
                exp.tipo_documento = tipo_doc_default
                modificado = True
            if exp.tipo_supervision is None:
                exp.tipo_supervision = tipo_sup_default
                modificado = True
            if modificado:
                exp.save()
                reparados += 1

        self.stdout.write(self.style.SUCCESS(f"🔧 Expedientes reparados: {reparados}"))
        self.stdout.write(self.style.SUCCESS("\n✅ Catálogos actualizados y relaciones reparadas correctamente."))
