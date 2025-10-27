from django.contrib import admin
from django.utils.html import format_html
from .models import Restaurant, Table, Reservation, Tag, RestaurantDocument

class TableInline(admin.TabularInline):
    model = Table
    extra = 1

@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ['name', 'cuisine_type', 'phone', 'created_at']
    list_filter = ['cuisine_type', 'created_at']
    search_fields = ['name', 'address']
    inlines = [TableInline]

@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ['table_number', 'restaurant', 'capacity', 'price_per_hour']
    list_filter = ['restaurant']

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'table', 'reservation_date', 'status']
    list_filter = ['status', 'reservation_date']

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name']

@admin.register(RestaurantDocument)
class RestaurantDocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'restaurant', 'uploaded_at']