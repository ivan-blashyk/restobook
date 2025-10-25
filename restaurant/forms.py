from django import forms
from .models import Restaurant, Table

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