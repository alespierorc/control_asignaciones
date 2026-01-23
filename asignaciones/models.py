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

class Expediente(models.Model):
    """Registro detallado de expedientes asignados a supervisores."""

    ESTADOS = [
        ("EN_PROCESO", "En proceso"),
        ("PENDIENTE", "Pendiente"),
        ("CONCLUIDO", "Concluido"),
    ]

    siged = models.CharField(max_length=50, unique=True, verbose_name="N° SIGED")
    codigo = models.CharField(max_length=50, blank=True)
    codigo_actividad = models.CharField(max_length=50, blank=True)
    razon_social = models.CharField(max_length=200, blank=True)
    carta_linea = models.CharField(max_length=100, blank=True)
    visita_decision = models.CharField(max_length=2, choices=[("SI", "Sí"), ("NO", "No")], default="NO")

    fecha_asignacion = models.DateField(null=False, blank=False)
    fecha_visita = models.DateField(null=True, blank=True)
    fecha_derivacion = models.DateField(null=True, blank=True)
    observaciones = models.TextField(blank=True)

    estado = models.CharField(max_length=20, choices=ESTADOS, default="EN_PROCESO")
    concluido = models.BooleanField(default=False)

    # 🔗 Relaciones
    contrato = models.ForeignKey(Contrato, on_delete=models.PROTECT)
    oficina = models.ForeignKey(OficinaRegional, on_delete=models.PROTECT)
    supervisor = models.ForeignKey(
        User, on_delete=models.PROTECT,
        limit_choices_to={"groups__name": "Supervisor"}
    )
    tipo_supervision = models.ForeignKey(TipoSupervision, on_delete=models.SET_NULL, null=True, blank=True)
    tipo_documento = models.ForeignKey(TipoDocumento, on_delete=models.SET_NULL, null=True, blank=True)

    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Expediente"
        verbose_name_plural = "Expedientes"

    def __str__(self):
        return f"{self.siged} ({self.get_estado_display()})"


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
