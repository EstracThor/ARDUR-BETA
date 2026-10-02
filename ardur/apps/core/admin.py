from django.contrib import admin
from django.apps import apps

class DomainReadOnlyAdmin(admin.ModelAdmin):
    """Las escrituras usan servicios para mantener permisos, transacciones y auditoría."""
    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False
    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.groups.filter(name='ADMINISTRADOR').exists()

for model in apps.get_models():
    if model.__module__.startswith('ardur.apps.') and not admin.site.is_registered(model):
        admin.site.register(model, DomainReadOnlyAdmin)
