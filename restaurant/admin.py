from django.contrib import admin
from django.http import HttpResponse
from django.utils.html import format_html
from .models import Restaurant, Table, Reservation, Tag, RestaurantDocument
from .utils import generate_restaurant_pdf

# ✅ ИМПОРТЫ ДЛЯ ЭКСПОРТА (ПРОСТЫЕ БЕЗ ОШИБОК)
from import_export.admin import ImportExportModelAdmin
from import_export import resources

class TableInline(admin.TabularInline):
    model = Table
    extra = 1

class RestaurantDocumentInline(admin.TabularInline):
    model = RestaurantDocument
    extra = 1
    readonly_fields = ['uploaded_at']

# ✅ РЕСУРС ДЛЯ ЭКСПОРТА РЕСТОРАНОВ
class RestaurantResource(resources.ModelResource):
    class Meta:
        model = Restaurant
        fields = ('id', 'name', 'cuisine_type', 'address', 'phone', 'created_at')
    
    # ✅ 1. КАСТОМНЫЙ МЕТОД - ФИЛЬТРАЦИЯ ДАННЫХ
    def get_export_queryset(self):
        """Экспортировать только рестораны созданные за последний месяц"""
        from django.utils import timezone
        from datetime import timedelta
        month_ago = timezone.now() - timedelta(days=30)
        return Restaurant.objects.filter(created_at__gte=month_ago)
    
    # ✅ 2. КАСТОМНЫЙ МЕТОД - ПРЕОБРАЗОВАНИЕ ТИПА КУХНИ
    def dehydrate_cuisine_type(self, restaurant):
        """Преобразовать cuisine_type в читаемый формат"""
        return restaurant.get_cuisine_type_display()
    
    # ✅ 3. КАСТОМНЫЙ МЕТОД - ДОБАВИТЬ КОЛИЧЕСТВО СТОЛИКОВ
    def dehydrate_name(self, restaurant):
        """Добавить количество столиков к названию"""
        table_count = restaurant.tables.count()
        return f"{restaurant.name} ({table_count} столиков)"

# ✅ АДМИНКА РЕСТОРАНОВ С ЭКСПОРТОМ И ИСТОРИЕЙ
@admin.register(Restaurant)
class RestaurantAdmin(ImportExportModelAdmin):  # ← ВАЖНО: ImportExportModelAdmin
    resource_class = RestaurantResource
    
    # БАЗОВЫЕ НАСТРОЙКИ
    list_display = ['name', 'cuisine_type', 'phone', 'created_at']
    list_filter = ['cuisine_type', 'created_at']
    search_fields = ['name', 'address']
    inlines = [TableInline]
    
    # ✅ ПРОСТЫЕ ДЕЙСТВИЯ БЕЗ ФОРМАТИРОВАНИЯ
    actions = ['generate_pdf_report']
    
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

# ✅ РЕСУРС ДЛЯ ЭКСПОРТА СТОЛИКОВ
class TableResource(resources.ModelResource):
    class Meta:
        model = Table

@admin.register(Table)
class TableAdmin(ImportExportModelAdmin):  # ← ЭКСПОРТ ДЛЯ СТОЛИКОВ
    resource_class = TableResource
    list_display = ['table_number', 'restaurant', 'capacity', 'price_per_hour']

# ✅ РЕСУРС ДЛЯ ЭКСПОРТА БРОНИРОВАНИЙ
class ReservationResource(resources.ModelResource):
    class Meta:
        model = Reservation

@admin.register(Reservation)
class ReservationAdmin(ImportExportModelAdmin):  # ← ЭКСПОРТ ДЛЯ БРОНИРОВАНИЙ
    resource_class = ReservationResource
    list_display = ['id', 'user', 'table', 'reservation_date', 'status']

# ✅ ОСТАЛЬНЫЕ МОДЕЛИ (БЕЗ ЭКСПОРТА)
@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name']

@admin.register(RestaurantDocument)
class RestaurantDocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'restaurant', 'uploaded_at']