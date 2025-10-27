from django.contrib import admin
from django.http import HttpResponse
from django.utils.html import format_html
from .models import Restaurant, Table, Reservation, Tag, RestaurantDocument
from .utils import generate_restaurant_pdf

class TableInline(admin.TabularInline):
    model = Table
    extra = 1
    fields = ['table_number', 'capacity', 'price_per_hour']

class RestaurantDocumentInline(admin.TabularInline):
    model = RestaurantDocument
    extra = 1
    fields = ['title', 'document', 'uploaded_at']
    readonly_fields = ['uploaded_at']

@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ['name', 'cuisine_type', 'phone', 'image_preview', 'table_count', 'created_at']
    list_filter = ['cuisine_type', 'created_at', 'tags']
    search_fields = ['name', 'address', 'phone']
    readonly_fields = ['created_at', 'image_preview']
    filter_horizontal = ['tags']
    
    inlines = [TableInline, RestaurantDocumentInline]
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'description', 'cuisine_type', 'image', 'image_preview', 'website', 'tags')
        }),
        ('Контактная информация', {
            'fields': ('address', 'phone', 'opening_hours')
        }),
        ('Мета-информация', {
            'fields': ('created_by', 'created_at')
        }),
    )
    
    actions = ['generate_pdf_report', 'increase_prices_10_percent']
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100" height="75" style="object-fit: cover;" />', obj.image.url)
        return "—"
    image_preview.short_description = 'Превью'
    
    def table_count(self, obj):
        return obj.tables.count()
    table_count.short_description = 'Столиков'
    
    def generate_pdf_report(self, request, queryset):
        if len(queryset) == 1:
            restaurant = queryset.first()
            buffer = generate_restaurant_pdf(restaurant)
            
            response = HttpResponse(buffer, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="restaurant_{restaurant.id}.pdf"'
            return response
        else:
            self.message_user(request, "Выберите только один ресторан для генерации PDF")
    generate_pdf_report.short_description = "Сгенерировать PDF отчет"
    
    def increase_prices_10_percent(self, request, queryset):
        from django.db.models import F
        for restaurant in queryset:
            restaurant.tables.update(price_per_hour=F('price_per_hour') * 1.1)
        self.message_user(request, f"Цены увеличены на 10% для {queryset.count()} ресторанов")
    increase_prices_10_percent.short_description = "Увеличить цены на 10%"

@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ['table_number', 'restaurant', 'capacity', 'price_per_hour']
    list_filter = ['restaurant', 'capacity']
    search_fields = ['table_number', 'restaurant__name']
    list_editable = ['capacity', 'price_per_hour']

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'table_info', 'reservation_date', 'reservation_time', 'guests_count', 'status']
    list_filter = ['status', 'reservation_date', 'created_at']
    search_fields = ['user__username', 'table__restaurant__name']
    readonly_fields = ['created_at']
    list_editable = ['status']
    
    actions = ['mark_as_confirmed', 'mark_as_cancelled']
    
    def table_info(self, obj):
        return f"{obj.table.restaurant.name} - Столик {obj.table.table_number}"
    table_info.short_description = 'Ресторан и столик'
    
    def mark_as_confirmed(self, request, queryset):
        updated = queryset.update(status='confirmed')
        self.message_user(request, f"{updated} бронирований подтверждено")
    mark_as_confirmed.short_description = "Подтвердить бронирования"
    
    def mark_as_cancelled(self, request, queryset):
        updated = queryset.update(status='cancelled')
        self.message_user(request, f"{updated} бронирований отменено")
    mark_as_cancelled.short_description = "Отменить бронирования"

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'restaurant_count']
    search_fields = ['name']
    
    def restaurant_count(self, obj):
        return obj.restaurants.count()
    restaurant_count.short_description = 'Ресторанов'

@admin.register(RestaurantDocument)
class RestaurantDocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'restaurant', 'uploaded_at']
    list_filter = ['uploaded_at']
    search_fields = ['title', 'restaurant__name']
    readonly_fields = ['uploaded_at']