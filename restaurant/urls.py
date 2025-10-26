from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('demo/', views.demo_page, name='demo'),
    path('login/', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('search/', views.search_restaurants, name='search_restaurants'),
    path('restaurants/', views.all_restaurants, name='all_restaurants'),
    path('restaurants/add/', views.restaurant_create, name='restaurant_create'),
    path('restaurants/<int:restaurant_id>/', views.restaurant_detail, name='restaurant_detail'),
    path('restaurants/<int:restaurant_id>/edit/', views.restaurant_edit, name='restaurant_edit'),
    path('restaurants/<int:restaurant_id>/delete/', views.restaurant_delete, name='restaurant_delete'),
    path('reservations/', views.user_reservations, name='user_reservations'),
    path('reservations/<int:table_id>/book/', views.make_reservation, name='make_reservation'),
    path('reservations/<int:reservation_id>/cancel/', views.cancel_reservation, name='cancel_reservation'),
]