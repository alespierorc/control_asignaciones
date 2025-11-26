from django.db.models.signals import post_migrate
from django.contrib.auth.models import Group
from django.dispatch import receiver

@receiver(post_migrate)
def crear_roles_por_defecto(sender, **kwargs):
    """
    Crea los grupos (roles) básicos del sistema si no existen.
    Se ejecuta automáticamente después de 'migrate'.
    """
    if sender.name == "asignaciones":  # Evita que se ejecute en todas las apps
        roles = ["AdminGeneral", "AdminSimple", "Coordinador", "Supervisor"]
        for rol in roles:
            grupo, creado = Group.objects.get_or_create(name=rol)
            if creado:
                print(f"✅ Rol creado: {rol}")
