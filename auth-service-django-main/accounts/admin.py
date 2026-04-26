from django.contrib import admin
from .models import Utilisateur

@admin.register(Utilisateur)
class UtilisateurAdmin(admin.ModelAdmin):
    list_display = ('email', 'nom', 'prenom', 'role', 'is_active')
    list_filter = ('role', 'is_active')
    search_fields = ('email', 'nom', 'prenom')
    readonly_fields = ('date_joined', 'last_login')
    
    fieldsets = (
        ('Informations personnelles', {
            'fields': ('email', 'nom', 'prenom', 'telephone', 'entreprise')
        }),
        ('Rôle et permissions', {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser')
        }),
        ('Dates', {
            'fields': ('date_joined', 'last_login'),
            'classes': ('collapse',)
        }),
    )