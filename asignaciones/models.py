# ============================================================
#                      MODELS.PY - SERMINCO
# ============================================================
# Modelos oficiales del sistema de control de asignaciones
# Roles: AdministradorLider, Administrador, Coordinador, Supervisor
# ============================================================

from django.db import models
from django.contrib.auth.models import User, Group


# ============================================================
#                  MODELOS AUXILIARES
# ============================================================

class OficinaRegional(models.Model):
    """Representa una oficina regional de SERMINCO."""
    nombre = models.CharField(max_length=120, unique=True)

    def __str__(self):
        return self.nombre


class TipoSupervision(models.Model):
    """Tipos de supervisión (ORDINARIA, INOPINADA, etc.)"""
    nombre = models.CharField(max_length=120, unique=True)

    class Meta:
        verbose_name = "Tipo de Supervisión"
        verbose_name_plural = "Tipos de Supervisión"

    def __str__(self):
        return self.nombre


class TipoDocumento(models.Model):
    """Tipos de documentos (OFICIO, INFORME, etc.)"""
    nombre = models.CharField(max_length=120, unique=True)

    class Meta:
        verbose_name = "Tipo de Documento"
        verbose_name_plural = "Tipos de Documento"

    def __str__(self):
        return self.nombre


class Contrato(models.Model):
    """Cada contrato pertenece a una oficina regional."""
    numero = models.CharField(max_length=50)
    descripcion = models.CharField(max_length=200, blank=True)
    oficina = models.ForeignKey(OficinaRegional, on_delete=models.PROTECT, related_name="contratos")

    class Meta:
        unique_together = ("numero", "oficina")
        verbose_name = "Contrato"
        verbose_name_plural = "Contratos"

    def __str__(self):
        return f"{self.numero} — {self.oficina.nombre}"


# ============================================================
#                  MODELO PRINCIPAL: EXPEDIENTE
# ============================================================

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Expediente(models.Model):
    """Registro detallado de expedientes asignados a supervisores."""

    # =====================================================
    # ESTADOS
    # =====================================================

    ESTADOS = [
        ("EN_PROCESO", "En proceso"),
        ("PENDIENTE", "Pendiente"),
        ("CONCLUIDO", "Concluido"),
    ]

    # =====================================================
    # CAMPOS BASE
    # =====================================================

    siged = models.CharField(max_length=50, unique=True, verbose_name="N° SIGED")
    codigo = models.CharField(max_length=50, blank=True)
    codigo_actividad = models.CharField(max_length=50, blank=True)
    razon_social = models.CharField(max_length=200, blank=True)
    carta_linea = models.CharField(max_length=100, blank=True)

    visita_decision = models.CharField(
        max_length=2,
        choices=[("SI", "Sí"), ("NO", "No")],
        default="NO"
    )

    # =====================================================
    # FECHAS
    # =====================================================

    fecha_asignacion = models.DateField()

    # ❗ NO intervienen en el cálculo de plazo
    fecha_visita = models.DateField(null=True, blank=True)
    fecha_derivacion = models.DateField(null=True, blank=True)

    # ✅ Fecha límite — base del plazo
    fecha_limite = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha límite de cumplimiento"
    )

    # =====================================================
    # CONTROL
    # =====================================================

    observaciones = models.TextField(blank=True)

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default="EN_PROCESO"
    )

    concluido = models.BooleanField(default=False)

    # =====================================================
    # RELACIONES
    # =====================================================

    contrato = models.ForeignKey("Contrato", on_delete=models.PROTECT)
    oficina = models.ForeignKey("OficinaRegional", on_delete=models.PROTECT)

    supervisor = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        limit_choices_to={"groups__name": "Supervisor"}
    )

    tipo_supervision = models.ForeignKey(
        "TipoSupervision",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    tipo_documento = models.ForeignKey(
        "TipoDocumento",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # =====================================================
    # AUDITORÍA
    # =====================================================

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # =====================================================
    # META
    # =====================================================

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Expediente"
        verbose_name_plural = "Expedientes"

    def __str__(self):
        return f"{self.siged} ({self.get_estado_display()})"

    # =====================================================
    # ================= PLAZO — CÁLCULO ===================
    # =====================================================

    def plazo_total_dias(self):
        """
        Duración fija del plazo
        fecha_limite - fecha_asignacion
        """
        if self.fecha_asignacion and self.fecha_limite:
            return (self.fecha_limite - self.fecha_asignacion).days
        return None

    def dias_restantes(self):
        """
        Plazo dinámico contra HOY
        Puede ser negativo
        """
        if not self.fecha_limite:
            return None

        hoy = timezone.now().date()
        return (self.fecha_limite - hoy).days

    def dias_tardanza(self):
        """
        Días pasados del plazo
        """
        dias = self.dias_restantes()
        if dias is not None and dias < 0:
            return abs(dias)
        return 0

    def esta_vencido(self):
        dias = self.dias_restantes()
        return dias is not None and dias < 0

    def esta_en_plazo(self):
        dias = self.dias_restantes()
        return dias is not None and dias >= 0

    # =====================================================
    # RESULTADO LÓGICO DEL PLAZO
    # =====================================================

    def resultado_plazo(self):

        if not self.fecha_limite:
            return "SIN_LIMITE"

        dias = self.dias_restantes()

        if self.estado == "CONCLUIDO" or self.concluido:

            if self.fecha_derivacion:
                diff = (self.fecha_limite - self.fecha_derivacion).days
                if diff >= 0:
                    return "CONCLUIDO_EN_PLAZO"
                return "CONCLUIDO_TARDE"

            return "CONCLUIDO"

        if dias is not None and dias < 0:
            return "VENCIDO"

        return "EN_CURSO"

    # =====================================================
    # TEXTO UI PERSISTENTE
    # =====================================================

    def texto_plazo_ui(self):
        """
        Devuelve (texto, color)
        """

        if not self.fecha_limite:
            return "—", "neutral"

        hoy = timezone.now().date()

        # =====================
        # SI YA CONCLUYÓ
        # =====================

        if self.estado == "CONCLUIDO" or self.concluido:

            if not self.fecha_derivacion:
                return "Terminado", "verde"

            diff = (self.fecha_limite - self.fecha_derivacion).days

            if diff >= 0:
                return f"Terminado antes ({diff} días)", "verde"
            else:
                return f"Terminado pasando ({abs(diff)} días)", "rojo"

        # =====================
        # NO CONCLUIDO
        # =====================

        dias = (self.fecha_limite - hoy).days

        if dias == 0:
            return "Hoy", "amarillo"

        if dias > 0:
            return f"{dias} días", "amarillo"

        return f"{dias} días", "rojo"

    def clase_plazo_badge(self):

        _, color = self.texto_plazo_ui()

        return {
            "verde": "plazo-ok",
            "rojo": "plazo-vencido",
            "amarillo": "plazo-alerta",
            "neutral": ""
        }.get(color, "")

    # =====================================================
    # PAYLOAD LISTO PARA AJAX
    # =====================================================

    def plazo_ui_payload(self):

        texto, _ = self.texto_plazo_ui()

        return {
            "plazo_texto": texto,
            "plazo_clase": self.clase_plazo_badge(),
            "dias_restantes": self.dias_restantes(),
            "dias_tardanza": self.dias_tardanza(),
        }

    # =====================================================
    # SAVE HOOK
    # =====================================================

    def save(self, *args, **kwargs):

        if self.estado == "CONCLUIDO":
            self.concluido = True

        super().save(*args, **kwargs)


# ============================================================
#                  MENSAJERÍA INTERNA
# ============================================================
class Mensaje(models.Model):
    remitente = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="mensajes_enviados"
    )
    destinatario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="mensajes_recibidos"
    )

    asunto = models.CharField(max_length=200)
    cuerpo = models.TextField()
    leido = models.BooleanField(default=False)
    creado_en = models.DateTimeField(auto_now_add=True)

    eliminado_por_remitente = models.BooleanField(default=False)
    eliminado_por_destinatario = models.BooleanField(default=False)

    class Meta:
        ordering = ["-creado_en"]

    def __str__(self):
        return f"{self.asunto} ({self.remitente} → {self.destinatario})"


# ============================================================
#                        ANUNCIOS
# ============================================================

class Anuncio(models.Model):

    PRIORIDAD_CHOICES = [
        ("normal", "Normal"),
        ("importante", "Importante"),
        ("critico", "Crítico"),
    ]

    TIPO_CHOICES = [
        ("general", "General"),
        ("grupo", "Grupo"),
        ("individual", "Individual"),
    ]

    titulo = models.CharField(max_length=255)
    contenido = models.TextField()

    remitente = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="anuncios_enviados"
    )

    destinatario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="anuncios_recibidos"
    )

    grupo_destino = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default="general")
    prioridad = models.CharField(max_length=20, choices=PRIORIDAD_CHOICES, default="normal")

    fecha_inicio = models.DateTimeField(null=True, blank=True)
    fecha_fin = models.DateTimeField(null=True, blank=True)

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha_creacion"]

    def __str__(self):
        return self.titulo

class AnuncioLectura(models.Model):
    anuncio = models.ForeignKey(
        Anuncio,
        on_delete=models.CASCADE,
        related_name="lecturas"
    )
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="anuncios_leidos"
    )
    fecha_lectura = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("anuncio", "usuario")

    def __str__(self):
        return f"{self.usuario} leyó {self.anuncio}"

class AnuncioEliminado(models.Model):
    anuncio = models.ForeignKey(
        Anuncio,
        on_delete=models.CASCADE,
        related_name="eliminaciones"
    )
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="anuncios_eliminados"
    )
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("anuncio", "usuario")

    def __str__(self):
        return f"{self.usuario} eliminó {self.anuncio}"
