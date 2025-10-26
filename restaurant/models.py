from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone

class Restaurant(models.Model):
    CUISINE_TYPES = [
        ('italian', 'Итальянская'),
        ('japanese', 'Японская'),
        ('russian', 'Русская'),
        ('french', 'Французская'),
        ('chinese', 'Китайская'),
        ('georgian', 'Грузинская'),
        ('american', 'Американская'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField()
    address = models.TextField()
    phone = models.CharField(max_length=20)
    cuisine_type = models.CharField(max_length=50, choices=CUISINE_TYPES)
    opening_hours = models.CharField(max_length=100, default='10:00-22:00')
    image = models.ImageField(upload_to='restaurants/', blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('restaurant_detail', kwargs={'restaurant_id': self.id})
    
    def can_edit(self, user):
        """Проверка прав на редактирование"""
        if not user or not user.is_authenticated:
            return False
        # Только staff может редактировать
        return user.is_staff

    def can_delete(self, user):
        """Проверка прав на удаление"""
        if not user or not user.is_authenticated:
            return False
        # Только staff может удалять
        return user.is_staff

    def can_create(self, user):
        """Проверка прав на создание ресторана"""
        if not user or not user.is_authenticated:
            return False
        # Только staff может создавать рестораны
        return user.is_staff

    def show_edit_button(self, user):
        """Показывать ли кнопку редактирования"""
        return self.can_edit(user)

    def show_delete_button(self, user):
        """Показывать ли кнопку удаления"""
        return self.can_delete(user)

    def show_create_button(self, user):
        """Показывать ли кнопку создания"""
        return self.can_create(user)

class Table(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    table_number = models.CharField(max_length=10)
    capacity = models.IntegerField()
    price_per_hour = models.DecimalField(max_digits=8, decimal_places=2, default=500.00)

    def __str__(self):
        return f"Столик {self.table_number}"
    
    def get_absolute_url(self):
        return reverse('restaurant_detail', kwargs={'restaurant_id': self.restaurant.id})

class Reservation(models.Model):
    STATUS_CHOICES = [
        ('confirmed', 'Подтверждено'),
        ('pending', 'Ожидание'),
        ('cancelled', 'Отменено'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    table = models.ForeignKey(Table, on_delete=models.CASCADE)
    reservation_date = models.DateField()
    reservation_time = models.TimeField()
    guests_count = models.IntegerField()
    special_requests = models.TextField(blank=True, verbose_name='Особые пожелания')  # ДОБАВЛЕНО ПОЛЕ
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Бронь #{self.id}"
    
    def can_edit(self, user):
        if not user or not user.is_authenticated:
            return False
        return user.is_staff or user == self.user