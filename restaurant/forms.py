from django import forms
from .models import Restaurant, Table, Reservation
from django.utils import timezone
from datetime import datetime, time

class RestaurantForm(forms.ModelForm):
    class Meta:
        model = Restaurant
        fields = ['name', 'description', 'address', 'phone', 'cuisine_type', 'opening_hours', 'image']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название ресторана'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Описание ресторана'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Адрес'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+7 (XXX) XXX-XX-XX'}),
            'cuisine_type': forms.Select(attrs={'class': 'form-control'}),
            'opening_hours': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '10:00-22:00'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'name': 'Название ресторана',
            'description': 'Описание',
            'address': 'Адрес',
            'phone': 'Телефон',
            'cuisine_type': 'Тип кухни',
            'opening_hours': 'Часы работы',
            'image': 'Фотография',
        }

class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ['reservation_date', 'reservation_time', 'guests_count', 'special_requests']
        widgets = {
            'reservation_date': forms.DateInput(attrs={
                'class': 'form-control', 
                'type': 'date',
                'min': datetime.now().strftime('%Y-%m-%d')
            }),
            'reservation_time': forms.TimeInput(attrs={
                'class': 'form-control', 
                'type': 'time'
            }),
            'guests_count': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 20
            }),
            'special_requests': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3,
                'placeholder': 'Особые пожелания (аллергии, праздник и т.д.)'
            }),
        }
        labels = {
            'reservation_date': 'Дата бронирования',
            'reservation_time': 'Время бронирования',
            'guests_count': 'Количество гостей',
            'special_requests': 'Особые пожелания',
        }

    def clean(self):
        cleaned_data = super().clean()
        reservation_date = cleaned_data.get('reservation_date')
        reservation_time = cleaned_data.get('reservation_time')
        guests_count = cleaned_data.get('guests_count')
        
        # Проверка что дата не в прошлом
        if reservation_date and reservation_date < timezone.now().date():
            raise forms.ValidationError("Нельзя забронировать столик на прошедшую дату")
        
        # Проверка времени (рестораны работают с 10:00 до 23:00)
        if reservation_time:
            if reservation_time < time(10, 0) or reservation_time > time(23, 0):
                raise forms.ValidationError("Рестораны работают с 10:00 до 23:00")
        
        return cleaned_data