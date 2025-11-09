from django.contrib import admin
from .models import Category, MenuItem, Order, OrderItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon')
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'cooking_time', 'is_available')
    list_filter = ('category', 'is_available')
    search_fields = ('name', 'description')
    list_editable = ('price', 'cooking_time', 'is_available')
    autocomplete_fields = ('category',)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('menu_item', 'quantity', 'price_at_order')
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'table_number', 'status', 'total_price', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__mobile', 'table_number', 'user__first_name', 'user__last_name')
    readonly_fields = ('total_price', 'created_at', 'user', 'table_number', 'special_requests')
    inlines = [OrderItemInline]

    def has_add_permission(self, request):
        return False  # فقط از فرانت ثبت بشه

    def has_change_permission(self, request, obj=None):
        return False  # فقط وضعیت تغییر کنه، نه محتوا