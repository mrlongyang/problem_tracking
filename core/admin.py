from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _  # Optional for i18n
from .models import (
    Department, User, Problem, Solution,
    SolutionAttachment, Tag, ProblemTag, UserGroup, Role, Menu, Permission, ProblemAttachment, Module
)
from django.contrib.auth.admin import UserAdmin

# Register all other models
admin.site.register(Department)
admin.site.register(Problem)
admin.site.register(ProblemAttachment)
admin.site.register(Solution)
admin.site.register(SolutionAttachment)     
admin.site.register(Tag)
admin.site.register(ProblemTag)
admin.site.register(UserGroup)
admin.site.register(Role)
admin.site.register(Menu)
admin.site.register(Permission)
admin.site.register(Module)
# admin.site.register(User, UserAdmin)
@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    model = User
    list_display = ('email', 'name', 'role', 'user_group', 'is_staff')
    ordering = ('email',)
    search_fields = ('email', 'name')
    list_filter = ('role', 'is_staff')

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('name', 'department', 'role', 'user_group')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'department', 'role', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )

    # ✅ Explicitly clear inherited references
    filter_horizontal = ()  # ✅ This solves the error

