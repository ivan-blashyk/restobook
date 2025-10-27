from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from .models import Restaurant, Table, Reservation
from .serializers import RestaurantSerializer, TableSerializer, ReservationSerializer

class RestaurantViewSet(viewsets.ModelViewSet):
    queryset = Restaurant.objects.all()
    serializer_class = RestaurantSerializer
    
    # ✅ ПРАВИЛЬНАЯ НАСТРОЙКА ФИЛЬТРАЦИИ И ПОИСКА
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    # ✅ ФИЛЬТРАЦИЯ ПО КОНКРЕТНЫМ ПОЛЯМ
    filterset_fields = {
        'cuisine_type': ['exact'],  # ТОЧНОЕ СОВПАДЕНИЕ
        'tags': ['exact'],          # ФИЛЬТРАЦИЯ ПО ТЕГАМ
    }
    
    # ✅ ПОИСК ПО НЕСКОЛЬКИМ ПОЛЯМ
    search_fields = ['name', 'description', 'address']
    
    # ✅ СОРТИРОВКА
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    @action(detail=False, methods=['get'])
    def popular(self, request):
        """Популярные рестораны (с наибольшим количеством бронирований)"""
        week_ago = timezone.now().date() - timedelta(days=7)
        
        popular_restaurants = Restaurant.objects.annotate(
            reservation_count=Count('tables__reservations', 
                                  filter=Q(tables__reservations__reservation_date__gte=week_ago))
        ).filter(reservation_count__gt=0).order_by('-reservation_count')[:5]
        
        serializer = self.get_serializer(popular_restaurants, many=True)
        return Response({
            'message': 'Самые популярные рестораны за неделю',
            'count': len(popular_restaurants),
            'results': serializer.data
        })
    
    # ✅ ВТОРОЕ КАСТОМНОЕ ДЕЙСТВИЕ
    @action(detail=True, methods=['post'])
    def add_tag(self, request, pk=None):
        """Добавление тега к ресторану"""
        restaurant = self.get_object()
        tag_name = request.data.get('tag_name')
        
        if not tag_name:
            return Response({'error': 'Укажите tag_name'}, status=400)
        
        # Создаем или получаем тег
        from .models import Tag
        tag, created = Tag.objects.get_or_create(name=tag_name)
        
        # Добавляем тег к ресторану
        restaurant.tags.add(tag)
        
        return Response({
            'message': f'Тег "{tag_name}" добавлен к ресторану',
            'restaurant': restaurant.name,
            'tag_added': tag_name
        })

class TableViewSet(viewsets.ModelViewSet):
    queryset = Table.objects.all()
    serializer_class = TableSerializer
    
    # ✅ ФИЛЬТРАЦИЯ ДЛЯ СТОЛИКОВ
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['restaurant', 'capacity']

class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer
    
    # ✅ ФИЛЬТРАЦИЯ ДЛЯ БРОНИРОВАНИЙ
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['table', 'user', 'status', 'reservation_date']
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Отмена бронирования"""
        reservation = self.get_object()
        reservation.status = 'cancelled'
        reservation.save()
        
        return Response({
            'message': 'Бронирование успешно отменено',
            'reservation_id': reservation.id,
            'status': 'cancelled'
        })
    
    # ✅ ВТОРОЕ КАСТОМНОЕ ДЕЙСТВИЕ ДЛЯ БРОНИРОВАНИЙ
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Предстоящие бронирования"""
        today = timezone.now().date()
        upcoming_reservations = Reservation.objects.filter(
            reservation_date__gte=today,
            status__in=['confirmed', 'pending']
        ).order_by('reservation_date', 'reservation_time')[:10]
        
        serializer = self.get_serializer(upcoming_reservations, many=True)
        return Response({
            'message': 'Предстоящие бронирования',
            'count': upcoming_reservations.count(),
            'results': serializer.data
        })