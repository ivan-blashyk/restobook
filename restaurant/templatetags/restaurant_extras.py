from django import template
from django.utils import timezone
from django.db.models import Count, Q  # ✅ ДОБАВИТЬ ИМПОРТ Q
from ..models import Restaurant, Reservation

register = template.Library()

@register.simple_tag
def current_time(format_string):
    """✅ Простой шаблонный тег - ТЕКУЩЕЕ ВРЕМЯ"""
    return timezone.now().strftime(format_string)

@register.simple_tag(takes_context=True)
def user_reservation_count(context):
    """✅ Шаблонный тег с контекстными переменными - КОЛИЧЕСТВО БРОНИЙ"""
    request = context['request']
    if request.user.is_authenticated:
        return Reservation.objects.filter(user=request.user).count()
    return 0

@register.inclusion_tag('restaurant/popular_restaurants.html')
def show_popular_restaurants(count=5):
    """✅ Шаблонный тег, возвращающий набор запросов - ПОПУЛЯРНЫЕ РЕСТОРАНЫ"""
    week_ago = timezone.now().date() - timezone.timedelta(days=7)
    
    # ✅ ИСПРАВЛЕННАЯ СТРОКА - убрано models.Q, используется просто Q
    restaurants = Restaurant.objects.annotate(
        reservation_count=Count('tables__reservations', 
                              filter=Q(tables__reservations__reservation_date__gte=week_ago))
    ).filter(reservation_count__gt=0).order_by('-reservation_count')[:count]
    
    return {'restaurants': restaurants}

@register.filter
def format_phone(value):
    """✅ Дополнительный фильтр для форматирования телефона"""
    if value and len(value) == 11 and value.isdigit():
        return f"+7 ({value[1:4]}) {value[4:7]}-{value[7:9]}-{value[9:]}"
    return value

@register.simple_tag
def restaurant_count():
    """✅ Дополнительный тег - количество ресторанов"""
    return Restaurant.objects.count()

@register.simple_tag(takes_context=True)
def user_has_reservations(context):
    """✅ Дополнительный тег - проверка есть ли брони у пользователя"""
    request = context['request']
    if request.user.is_authenticated:
        return Reservation.objects.filter(user=request.user).exists()
    return False