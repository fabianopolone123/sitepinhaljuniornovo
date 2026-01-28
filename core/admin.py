from django.contrib import admin

from .models import Adventurer, DirectorApplication, Responsible


@admin.register(Responsible)
class ResponsibleAdmin(admin.ModelAdmin):
    list_display = ("user", "cpf", "telefone", "whatsapp")


@admin.register(Adventurer)
class AdventurerAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "responsible", "birth_date")
    list_filter = ("responsible",)


@admin.register(DirectorApplication)
class DirectorApplicationAdmin(admin.ModelAdmin):
    list_display = ("responsible", "full_name", "created_at")
    list_filter = ("created_at",)
