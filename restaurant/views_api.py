from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Restaurant, Table, Reservation
from .serializers import RestaurantSerializer, TableSerializer, ReservationSerializer

class RestaurantViewSet(viewsets.ModelViewSet):
    queryset = Restaurant.objects.all()
    serializer_class = RestaurantSerializer
    
    @action(detail=False, methods=['get'])
    def popular(self, request):
        return Response({"message": "Популярные рестораны"})

class TableViewSet(viewsets.ModelViewSet):
    queryset = Table.objects.all()
    serializer_class = TableSerializer

class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        reservation = self.get_object()
        reservation.status = 'cancelled'
        reservation.save()
        return Response({"message": "Бронирование отменено"})