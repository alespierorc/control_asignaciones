from django.contrib import admin
from .models import OficinaRegional

@admin.register(OficinaRegional)
class OficinaRegionalAdmin(admin.ModelAdmin):
    list_display = ("nombre",)
    search_fields = ("nombre",)

