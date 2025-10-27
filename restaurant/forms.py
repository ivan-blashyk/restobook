from django import forms
from .models import Restaurant, Table, Reservation
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, time
from django.utils.translation import gettext_lazy as _

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'})
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Имя'})
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Фамилия'})
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Имя пользователя'}),
        }
        labels = {
            'username': _('Имя пользователя'),
            'email': _('Email'),
            'first_name': _('Имя'),
            'last_name': _('Фамилия'),
        }
        help_texts = {
            'username': _('Только буквы, цифры и @/./+/-/_.'),
        }
        error_messages = {
            'username': {
                'unique': _('Пользователь с таким именем уже существует.'),
            },
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Пароль'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Подтверждение пароля'})

    class Media:
        css = {
            'all': ('css/auth-forms.css',)
        }

class RestaurantForm(forms.ModelForm):
    class Meta:
        model = Restaurant
        fields = ['name', 'description', 'address', 'phone', 'cuisine_type', 'opening_hours', 'image', 'website', 'tags']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название ресторана'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Описание ресторана'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Адрес'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+7 (XXX) XXX-XX-XX'}),
            'cuisine_type': forms.Select(attrs={'class': 'form-control'}),
            'opening_hours': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '10:00-22:00'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://example.com'}),
            'tags': forms.SelectMultiple(attrs={'class': 'form-control'}),
        }
        labels = {
            'name': 'Название ресторана',
            'description': 'Описание',
            'address': 'Адрес',
            'phone': 'Телефон',
            'cuisine_type': 'Тип кухни',
            'opening_hours': 'Часы работы',
            'image': 'Фотография',
            'website': 'Веб-сайт',
            'tags': 'Теги',
        }
        help_texts = {
            'image': 'Рекомендуемый размер: 800x600px',
            'website': 'URL официального сайта ресторана',
        }

    def save(self, commit=True):
        restaurant = super().save(commit=False)
        if commit:
            restaurant.save()
            self.save_m2m()
        return restaurant

    class Media:
        css = {
            'all': ('css/restaurant-form.css',)
        }
        js = ('js/restaurant-form.js',)

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
        help_texts = {
            'guests_count': 'Максимальное количество гостей: 20',
        }

    def clean_reservation_date(self):
        reservation_date = self.cleaned_data.get('reservation_date')
        if reservation_date and reservation_date < timezone.now().date():
            raise forms.ValidationError("Нельзя забронировать столик на прошедшую дату")
        return reservation_date

    def clean_reservation_time(self):
        reservation_time = self.cleaned_data.get('reservation_time')
        if reservation_time:
            if reservation_time < time(10, 0) or reservation_time > time(23, 0):
                raise forms.ValidationError("Рестораны работают с 10:00 до 23:00")
        return reservation_time

    def clean_guests_count(self):
        guests_count = self.cleaned_data.get('guests_count')
        if guests_count and guests_count <= 0:
            raise forms.ValidationError("Количество гостей должно быть положительным числом")
        return guests_count

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data