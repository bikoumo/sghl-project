from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, CommentaireMedical

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # Ajout de 'is_mfa_enabled' ici pour le voir dans la liste des utilisateurs
    list_display = ('id', 'username', 'email', 'role', 'is_mfa_enabled', 'is_staff', 'is_active')
    
    list_filter = ('role', 'is_staff', 'is_active', 'is_mfa_enabled')
    search_fields = ('username', 'email')
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Informations Hospitalières', {
            'fields': ('role', 'service', 'phone', 'is_mfa_enabled')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Informations Hospitalières', {
            'fields': ('role', 'service', 'phone', 'is_mfa_enabled'),
        }),
    )

@admin.register(CommentaireMedical)
class CommentaireMedicalAdmin(admin.ModelAdmin):
    list_display = ('patient', 'medecin', 'date_creation')
    list_filter = ('date_creation',)
    search_fields = ('patient__username', 'medecin__username')