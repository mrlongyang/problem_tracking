from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    Department, User, Problem, Solution,
    SolutionAttachment, Tag, ProblemTag
)

# Register all other models
admin.site.register(Department)
admin.site.register(Problem)
admin.site.register(Solution)
admin.site.register(SolutionAttachment)
admin.site.register(Tag)
admin.site.register(ProblemTag)

# Register custom User admin
@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    model = User
    ordering = ('email',)
    list_display = ('email', 'name', 'role', 'department', 'is_staff')
    search_fields = ('email', 'name')
    list_filter = ('role', 'is_staff')

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('name', 'department', 'role')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login',)}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'department', 'role', 'password1', 'password2', 'is_staff', 'is_active')},
        ),
    )
