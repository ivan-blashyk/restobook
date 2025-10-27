from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.db.models import F, Q

class AvailableTableManager(models.Manager):
    """Кастомный менеджер для доступных столиков"""
    def get_queryset(self):
        today = timezone.now().date()
        return super().get_queryset().exclude(
            reservations__reservation_date=today,
            reservations__status__in=['confirmed', 'pending']
        )

class Tag(models.Model):
    """Теги для ресторанов"""
    name = models.CharField(max_length=50, unique=True, verbose_name=_('название'))
    description = models.TextField(blank=True, verbose_name=_('описание'))
    
    class Meta:
        verbose_name = _('тег')
        verbose_name_plural = _('теги')
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Restaurant(models.Model):
    CUISINE_TYPES = [
        ('italian', _('Итальянская')),
        ('japanese', _('Японская')),
        ('russian', _('Русская')),
        ('french', _('Французская')),
        ('chinese', _('Китайская')),
        ('georgian', _('Грузинская')),
        ('american', _('Американская')),
    ]
    
    name = models.CharField(max_length=100, verbose_name=_('название'))
    description = models.TextField(verbose_name=_('описание'))
    address = models.TextField(verbose_name=_('адрес'))
    phone = models.CharField(max_length=20, verbose_name=_('телефон'))
    cuisine_type = models.CharField(max_length=50, choices=CUISINE_TYPES, verbose_name=_('тип кухни'))
    opening_hours = models.CharField(max_length=100, default='10:00-22:00', verbose_name=_('часы работы'))
    image = models.ImageField(upload_to='restaurants/%Y/%m/%d/', blank=True, null=True, verbose_name=_('изображение'))
    website = models.URLField(blank=True, verbose_name=_('веб-сайт'))
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('создатель'))
    created_at = models.DateTimeField(default=timezone.now, verbose_name=_('дата создания'))
    
    # ManyToMany связь с тегами
    tags = models.ManyToManyField(Tag, blank=True, related_name='restaurants', verbose_name=_('теги'))

    class Meta:
        verbose_name = _('ресторан')
        verbose_name_plural = _('рестораны')
        ordering = ['name']

    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('restaurant_detail', kwargs={'restaurant_id': self.id})
    
    def get_available_tables(self, date, guests_count=2):
        """Собственный метод: получение доступных столиков"""
        busy_tables = Reservation.objects.filter(
            table__restaurant=self,
            reservation_date=date,
            status__in=['confirmed', 'pending']
        ).values_list('table_id', flat=True)
        
        return self.tables.exclude(id__in=busy_tables).filter(capacity__gte=guests_count)
    
    def increase_prices(self, percentage):
        """Использование F expression для обновления цен"""
        from django.db.models import F
        self.tables.update(price_per_hour=F('price_per_hour') * (1 + percentage/100))
    
    def can_edit(self, user):
        if not user or not user.is_authenticated:
            return False
        return user.is_staff

class RestaurantDocument(models.Model):
    """Модель для документов ресторана"""
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='documents')
    document = models.FileField(upload_to='restaurants/documents/%Y/%m/%d/', verbose_name=_('документ'))
    title = models.CharField(max_length=200, verbose_name=_('название'))
    uploaded_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        verbose_name = _('документ ресторана')
        verbose_name_plural = _('документы ресторанов')
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return self.title

class Table(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='tables')
    table_number = models.CharField(max_length=10, verbose_name=_('номер столика'))
    capacity = models.IntegerField(verbose_name=_('вместимость'))
    price_per_hour = models.DecimalField(max_digits=8, decimal_places=2, default=500.00, verbose_name=_('цена за час'))

    objects = models.Manager()
    available = AvailableTableManager()

    class Meta:
        verbose_name = _('столик')
        verbose_name_plural = _('столики')
        ordering = ['table_number']

    def __str__(self):
        return f"Столик {self.table_number}"
    
    def get_absolute_url(self):
        return reverse('restaurant_detail', kwargs={'restaurant_id': self.restaurant.id})

class Reservation(models.Model):
    STATUS_CHOICES = [
        ('confirmed', _('Подтверждено')),
        ('pending', _('Ожидание')),
        ('cancelled', _('Отменено')),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_reservations')
    table = models.ForeignKey(Table, on_delete=models.CASCADE, related_name='reservations')
    reservation_date = models.DateField(verbose_name=_('дата бронирования'))
    reservation_time = models.TimeField(verbose_name=_('время бронирования'))
    guests_count = models.IntegerField(verbose_name=_('количество гостей'))
    special_requests = models.TextField(blank=True, verbose_name=_('особые пожелания'))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name=_('статус'))
    created_at = models.DateTimeField(default=timezone.now, verbose_name=_('дата создания'))

    class Meta:
        verbose_name = _('бронирование')
        verbose_name_plural = _('бронирования')
        ordering = ['-reservation_date', '-reservation_time']

    def __str__(self):
        return f"Бронь #{self.id}"
    
    def get_absolute_url(self):
        return reverse('user_reservations')
    
    def can_edit(self, user):
        if not user or not user.is_authenticated:
            return False
        return user.is_staff or user == self.user