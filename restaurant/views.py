from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Count, Q, Avg, Max, Min
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.utils import timezone
from datetime import date, timedelta, time
from .models import Restaurant, Table, Reservation
from .forms import RestaurantForm, ReservationForm, CustomUserCreationForm

def home(request):
    today = date.today()
    
    # Виджет 1: Популярные рестораны (COUNT + агрегация)
    week_ago = today - timedelta(days=7)
    popular_restaurants = Restaurant.objects.annotate(
        reservation_count=Count('table__reservation', 
                              filter=Q(table__reservation__reservation_date__gte=week_ago))
    ).filter(reservation_count__gt=0).order_by('-reservation_count')[:4]
    
    # Виджет 2: Свободные столики на сегодня (exclude + filter)
    available_tables = Table.objects.exclude(
        reservation__reservation_date=today,
        reservation__status__in=['confirmed', 'pending']
    ).select_related('restaurant').order_by('-capacity')[:6]
    
    # Виджет 3: Рестораны с лучшей ценой (MIN агрегатная функция)
    affordable_restaurants = Restaurant.objects.annotate(
        min_price=Min('table__price_per_hour')
    ).filter(min_price__isnull=False).order_by('min_price')[:3]
    
    # Виджет 4: Рестораны с большими столиками (MAX агрегатная функция)
    large_tables_restaurants = Restaurant.objects.annotate(
        max_capacity=Max('table__capacity')
    ).filter(max_capacity__gte=6).order_by('-max_capacity')[:3]
    
    # Агрегатные функции для статистики
    stats = {
        'total_restaurants': Restaurant.objects.count(),
        'avg_table_price': Table.objects.aggregate(avg_price=Avg('price_per_hour'))['avg_price'] or 0,
        'max_capacity': Table.objects.aggregate(max_cap=Max('capacity'))['max_cap'] or 0,
        'min_price': Table.objects.aggregate(min_pr=Min('price_per_hour'))['min_pr'] or 0,
    }
    
    # Поиск
    search_results = None
    search_query = ""
    if 'q' in request.GET:
        search_query = request.GET['q']
        search_results = Restaurant.objects.filter(
            Q(name__icontains=search_query) | 
            Q(cuisine_type__icontains=search_query) |
            Q(address__icontains=search_query)
        ).distinct()
    
    context = {
        'popular_restaurants': popular_restaurants,
        'available_tables': available_tables,
        'affordable_restaurants': affordable_restaurants,
        'large_tables_restaurants': large_tables_restaurants,
        'stats': stats,
        'search_results': search_results,
        'search_query': search_query,
        'today': today,
    }
    return render(request, 'restaurant/home.html', context)

def restaurant_detail(request, restaurant_id):
    """Страница конкретного ресторана"""
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    tables = Table.objects.filter(restaurant=restaurant)
    reservations = Reservation.objects.filter(table__restaurant=restaurant)[:5]
    
    # Статистика ресторана
    stats = {
        'tables_count': tables.count(),
        'avg_capacity': tables.aggregate(avg_cap=Avg('capacity'))['avg_cap'] or 0,
        'min_price': tables.aggregate(min_pr=Min('price_per_hour'))['min_pr'] or 0,
        'max_capacity': tables.aggregate(max_cap=Max('capacity'))['max_cap'] or 0,
    }
    
    context = {
        'restaurant': restaurant,
        'tables': tables,
        'reservations': reservations,
        'stats': stats,
    }
    return render(request, 'restaurant/restaurant_detail.html', context)

def all_restaurants(request):
    """Страница со всеми ресторанами"""
    restaurants = Restaurant.objects.all()
    
    context = {
        'restaurants': restaurants,
    }
    return render(request, 'restaurant/all_restaurants.html', context)

@login_required
def restaurant_create(request):
    """Создание нового ресторана - ТОЛЬКО ДЛЯ STAFF"""
    # Проверяем является ли пользователь staff
    if not request.user.is_staff:
        messages.error(request, '❌ У вас нет прав для создания ресторанов. Только менеджеры могут добавлять рестораны.')
        return redirect('home')
    
    if request.method == 'POST':
        form = RestaurantForm(request.POST, request.FILES)
        if form.is_valid():
            restaurant = form.save(commit=False)
            restaurant.created_by = request.user
            restaurant.save()
            messages.success(request, f'✅ Ресторан "{restaurant.name}" успешно создан!')
            return redirect('restaurant_detail', restaurant_id=restaurant.id)
    else:
        form = RestaurantForm()
    
    context = {
        'form': form,
        'title': 'Добавить ресторан'
    }
    return render(request, 'restaurant/restaurant_form.html', context)

@login_required
def restaurant_edit(request, restaurant_id):
    """Редактирование ресторана - ТОЛЬКО ДЛЯ STAFF"""
    # Проверяем является ли пользователь staff
    if not request.user.is_staff:
        messages.error(request, '❌ У вас нет прав для редактирования ресторанов. Только менеджеры могут редактировать рестораны.')
        return redirect('restaurant_detail', restaurant_id=restaurant_id)
    
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    
    if request.method == 'POST':
        form = RestaurantForm(request.POST, request.FILES, instance=restaurant)
        if form.is_valid():
            form.save()
            messages.success(request, f'✅ Ресторан "{restaurant.name}" успешно обновлен!')
            return redirect('restaurant_detail', restaurant_id=restaurant.id)
    else:
        form = RestaurantForm(instance=restaurant)
    
    context = {
        'form': form,
        'restaurant': restaurant,
        'title': 'Редактировать ресторан'
    }
    return render(request, 'restaurant/restaurant_form.html', context)

@login_required
def restaurant_delete(request, restaurant_id):
    """Удаление ресторана - ТОЛЬКО ДЛЯ STAFF"""
    # Проверяем является ли пользователь staff
    if not request.user.is_staff:
        messages.error(request, '❌ У вас нет прав для удаления ресторанов. Только менеджеры могут удалять рестораны.')
        return redirect('restaurant_detail', restaurant_id=restaurant_id)
    
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    
    if request.method == 'POST':
        restaurant_name = restaurant.name
        restaurant.delete()
        messages.success(request, f'✅ Ресторан "{restaurant_name}" успешно удален!')
        return redirect('all_restaurants')
    
    context = {
        'restaurant': restaurant,
    }
    return render(request, 'restaurant/restaurant_confirm_delete.html', context)

def search_restaurants(request):
    """Страница поиска ресторанов"""
    restaurants = None
    query = ""
    
    if 'q' in request.GET:
        query = request.GET['q']
        restaurants = Restaurant.objects.filter(
            Q(name__icontains=query) | 
            Q(cuisine_type__icontains=query) |
            Q(address__icontains=query) |
            Q(description__icontains=query)
        ).distinct()
    
    # Агрегация для страницы поиска
    search_stats = {}
    if restaurants:
        search_stats = {
            'count': restaurants.count(),
            'cuisine_types': restaurants.values('cuisine_type').annotate(count=Count('id')),
            'avg_tables': Table.objects.filter(restaurant__in=restaurants).aggregate(avg_capacity=Avg('capacity'))['avg_capacity'] or 0,
        }
    
    context = {
        'restaurants': restaurants,
        'query': query,
        'search_stats': search_stats,
    }
    return render(request, 'restaurant/search.html', context)

def register(request):
    """Регистрация нового пользователя"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'🎉 Добро пожаловать, {user.username}! Регистрация прошла успешно.')
            return redirect('home')
        else:
            messages.error(request, '❌ Пожалуйста, исправьте ошибки в форме.')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'restaurant/register.html', {'form': form})

def custom_login(request):
    """Кастомная страница входа"""
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Добро пожаловать, {username}!')
                
                # Перенаправление на следующую страницу или на главную
                next_url = request.GET.get('next', 'home')
                return redirect(next_url)
        else:
            messages.error(request, '❌ Неверное имя пользователя или пароль.')
    else:
        form = AuthenticationForm()
    
    return render(request, 'restaurant/login.html', {'form': form})

def custom_logout(request):
    """Кастомный выход"""
    logout(request)
    messages.success(request, 'Вы успешно вышли из системы.')
    return redirect('home')

@login_required
def make_reservation(request, table_id):
    """Создание бронирования столика"""
    table = get_object_or_404(Table, id=table_id)
    
    if request.method == 'POST':
        form = ReservationForm(request.POST)
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.user = request.user
            reservation.table = table
            
            # Проверяем доступность столика
            conflicting_reservations = Reservation.objects.filter(
                table=table,
                reservation_date=reservation.reservation_date,
                reservation_time=reservation.reservation_time,
                status__in=['confirmed', 'pending']
            )
            
            if conflicting_reservations.exists():
                messages.error(request, '❌ Этот столик уже забронирован на выбранное время')
            elif reservation.guests_count > table.capacity:
                messages.error(request, f'❌ Столик вмещает только {table.capacity} гостей')
            else:
                reservation.save()
                messages.success(request, f'✅ Столик успешно забронирован на {reservation.reservation_date} в {reservation.reservation_time}')
                return redirect('restaurant_detail', restaurant_id=table.restaurant.id)
    else:
        # Устанавливаем минимальную дату - сегодня
        initial_data = {
            'reservation_date': timezone.now().date(),
            'guests_count': 2
        }
        form = ReservationForm(initial=initial_data)
    
    context = {
        'form': form,
        'table': table,
        'restaurant': table.restaurant
    }
    return render(request, 'restaurant/make_reservation.html', context)

@login_required
def user_reservations(request):
    """Страница с бронированиями пользователя"""
    reservations = Reservation.objects.filter(user=request.user).order_by('-reservation_date', '-reservation_time')
    
    context = {
        'reservations': reservations
    }
    return render(request, 'restaurant/user_reservations.html', context)

@login_required
def cancel_reservation(request, reservation_id):
    """Отмена бронирования"""
    reservation = get_object_or_404(Reservation, id=reservation_id, user=request.user)
    
    if request.method == 'POST':
        reservation.status = 'cancelled'
        reservation.save()
        messages.success(request, '✅ Бронирование отменено')
        return redirect('user_reservations')
    
    context = {
        'reservation': reservation
    }
    return render(request, 'restaurant/cancel_reservation.html', context)

def demo_page(request):
    """Демонстрационная страница"""
    return render(request, 'restaurant/demo.html')