from django.db import models
from django.contrib.auth.models import User


# ============================================================
#                  MODELOS PRINCIPALES
# ============================================================

class OficinaRegional(models.Model):
    """Representa una oficina regional."""
    nombre = models.CharField(max_length=120, unique=True)

    def __str__(self):
        return self.nombre


class Contrato(models.Model):
    """Cada contrato pertenece a una oficina regional."""
    numero = models.CharField(max_length=50)
    descripcion = models.CharField(max_length=200, blank=True)
    oficina = models.ForeignKey(OficinaRegional, on_delete=models.PROTECT, related_name="contratos")

    class Meta:
        unique_together = ("numero", "oficina")

    def __str__(self):
        return f"{self.numero} – {self.oficina.nombre}"


class Expediente(models.Model):
    """Registro de cada expediente (asignado por el coordinador)."""

    # ---- Opciones ----
    ESTADOS = [
        ("EN_PROCESO", "En proceso"),
        ("PENDIENTE", "Pendiente"),
        ("CONCLUIDO", "Concluido"),
    ]

    TIPO_SUPERVISION = [
        ("ORDINARIA", "Supervisión ordinaria"),
        ("INOPINADA", "Inspección inopinada"),
        ("ESPECIAL", "Supervisión especial"),
        ("OTRO", "Otro"),
    ]

    TIPO_DOCUMENTO = [
        ("OFICIO", "Oficio múltiple"),
        ("FICHA", "Ficha de registro de hidrocarburos"),
        ("INFORME", "Informe técnico"),
        ("OTRO", "Otro"),
    ]

    # ---- Campos principales ----
    siged = models.CharField(max_length=50, unique=True)
    codigo = models.CharField(max_length=50, blank=True)
    codigo_actividad = models.CharField(max_length=50, blank=True)
    razon_social = models.CharField(max_length=200, blank=True)
    oficina = models.ForeignKey(OficinaRegional, on_delete=models.PROTECT)
    contrato = models.ForeignKey(Contrato, on_delete=models.PROTECT)
    supervisor = models.ForeignKey(User, on_delete=models.PROTECT)
    tipo_supervision = models.CharField(max_length=20, choices=TIPO_SUPERVISION)
    tipo_documento = models.CharField(max_length=20, choices=TIPO_DOCUMENTO)
    carta_linea = models.CharField(max_length=100, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default="EN_PROCESO")
    visita_decision = models.CharField(max_length=2, blank=True)
    fecha_asignacion = models.DateField(null=False, blank=False)  # ← Obligatoria y manual
    fecha_visita = models.DateField(null=True, blank=True)
    fecha_derivacion = models.DateField(null=True, blank=True)
    observaciones = models.TextField(blank=True)
    concluido = models.BooleanField(default=False)  # ← nuevo campo

    # ---- Auditoría ----
    created_at = models.DateTimeField(auto_now_add=True)   # ← Fecha de creación
    updated_at = models.DateTimeField(auto_now=True)       # ← Última actualización

    def __str__(self):
        return f"{self.siged} ({self.get_estado_display()})"


# ============================================================
#                  MENSAJERÍA INTERNA
# ============================================================

class Mensaje(models.Model):
    """Mensajes internos entre usuarios (coordinador/supervisor)."""
    remitente = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="mensajes_enviados"
    )
    destinatario = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="mensajes_recibidos"
    )
    asunto = models.CharField(max_length=200)
    cuerpo = models.TextField()
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.asunto} ({self.remitente} → {self.destinatario})"


# ============================================================
#                  ANUNCIOS INTERNOS
# ============================================================

class Anuncio(models.Model):
    """Anuncios publicados por administradores o coordinadores."""
    DESTINOS = [
        ("SUP", "Supervisores"),
        ("COORD", "Coordinadores"),
        ("AMBOS", "Ambos"),
    ]

    titulo = models.CharField(max_length=200)
    contenido = models.TextField()
    destino = models.CharField(max_length=10, choices=DESTINOS)
    creador = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.titulo} ({self.destino})"
