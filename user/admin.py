from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, OTPCode


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('mobile', 'get_full_name', 'role', 'status', 'hire_date')
    list_filter = ('role', 'status', 'is_active')
    search_fields = ('mobile', 'first_name', 'last_name', 'national_code')
    ordering = ('-date_joined',)

    fieldsets = (
        (None, {'fields': ('mobile', 'password')}),
        ('اطلاعات شخصی', {'fields': ('first_name', 'last_name', 'national_code', 'birth_date', 'address')}),
        ('کار', {'fields': ('role', 'status', 'hire_date')}),
        ('مجوزها', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
    )

    add_fieldsets = (
        (None, {
            'fields': ('mobile', 'first_name', 'last_name', 'role', 'password1', 'password2'),
        }),
    )

    readonly_fields = ('date_joined', 'last_login')


@admin.register(OTPCode)
class OTPCodeAdmin(admin.ModelAdmin):
    list_display = ('mobile', 'code', 'created_at', 'expires_at')
    list_filter = ('created_at',)
    search_fields = ('mobile',)
    readonly_fields = ('mobile', 'code', 'created_at', 'expires_at')

    def has_add_permission(self, request):
        return False