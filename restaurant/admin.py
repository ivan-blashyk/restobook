from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Restaurant, Table, Reservation

# Кастомная админка для User
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)

# Кастомная админка для Restaurant
@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ('name', 'cuisine_type', 'phone', 'address_preview', 'created_by', 'created_at')
    list_filter = ('cuisine_type', 'created_at')
    search_fields = ('name', 'address', 'phone')
    readonly_fields = ('created_at',)
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'description', 'cuisine_type', 'image')
        }),
        ('Контактная информация', {
            'fields': ('address', 'phone', 'opening_hours')
        }),
        ('Мета-информация', {
            'fields': ('created_by', 'created_at')
        }),
    )
    
    def address_preview(self, obj):
        return obj.address[:50] + '...' if len(obj.address) > 50 else obj.address
    address_preview.short_description = 'Адрес'

# Кастомная админка для Table
@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ('table_number', 'restaurant', 'capacity', 'price_per_hour')
    list_filter = ('restaurant', 'capacity')
    search_fields = ('table_number', 'restaurant__name')
    list_editable = ('capacity', 'price_per_hour')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('restaurant')

# Кастомная админка для Reservation
@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'table_info', 'reservation_date', 'reservation_time', 'guests_count', 'status', 'created_at')
    list_filter = ('status', 'reservation_date', 'created_at')
    search_fields = ('user__username', 'table__restaurant__name', 'table__table_number')
    readonly_fields = ('created_at',)
    list_editable = ('status',)
    
    def table_info(self, obj):
        return f"{obj.table.restaurant.name} - Столик {obj.table.table_number}"
    table_info.short_description = 'Ресторан и столик'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'table', 'table__restaurant')

# Перерегистрируем User с кастомной админкой
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# Настройки админки
admin.site.site_header = "🍽 RestoBook - Панель управления"
admin.site.site_title = "RestoBook Admin"
admin.site.index_title = "Добро пожаловать в панель управления RestoBook"