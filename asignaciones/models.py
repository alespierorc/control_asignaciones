from django.db import models
from django.contrib.auth.models import User
from django.shortcuts import render, redirect

def home(request):
    return render(request, "home.html")

class OficinaRegional(models.Model):
    nombre = models.CharField(max_length=120, unique=True)
    def __str__(self): return self.nombre

class Contrato(models.Model):
    numero = models.CharField(max_length=50)
    descripcion = models.CharField(max_length=200, blank=True)
    oficina = models.ForeignKey(OficinaRegional, on_delete=models.PROTECT, related_name="contratos")
    class Meta:
        unique_together = ("numero", "oficina")
    def __str__(self): return f"{self.numero} - {self.oficina.nombre}"

class Expediente(models.Model):
    ESTADOS = [
        ("EN_PROCESO", "En proceso"),
        ("PENDIENTE", "Pendiente"),
        ("CONCLUIDO", "Concluido"),
    ]
    TIPO_SUPERVISION = [
        ("VISITA", "Visita"),
        ("VERIFICACION", "Verificación"),
        ("OTRO", "Otro"),
    ]
    TIPO_DOCUMENTO = [
        ("INFORME", "Informe"),
        ("ACTA", "Acta"),
        ("OFICIO", "Oficio"),
        ("OTRO", "Otro"),
    ]
    VISITA_CHOICES = [("SI", "Sí"), ("NO", "No")]

    siged = models.CharField("N.º SIGED", max_length=50, unique=True)
    oficina = models.ForeignKey(OficinaRegional, on_delete=models.PROTECT)
    contrato = models.ForeignKey(Contrato, on_delete=models.PROTECT)
    supervisor = models.ForeignKey(User, on_delete=models.PROTECT, related_name="expedientes_asignados")

    tipo_supervision = models.CharField(max_length=20, choices=TIPO_SUPERVISION)
    tipo_documento   = models.CharField(max_length=20, choices=TIPO_DOCUMENTO)
    carta_linea      = models.CharField(max_length=100, blank=True)

    # NUEVO: indicador de “¿se realizará visita?” (Sí/No)
    visita = models.CharField(max_length=2, choices=VISITA_CHOICES, blank=True)

    estado = models.CharField(max_length=20, choices=ESTADOS, default="EN_PROCESO")
    fecha_asignacion = models.DateField(auto_now_add=True)
    fecha_visita     = models.DateField(null=True, blank=True)
    fecha_derivacion = models.DateField(null=True, blank=True)
    observaciones    = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self): return f"{self.siged} ({self.estado})"
