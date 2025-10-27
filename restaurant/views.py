from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Count, Q, Avg, Max, Min, F
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.utils import timezone
from datetime import date, timedelta, time
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.db import transaction

from .models import Restaurant, Table, Reservation, Tag
from .forms import RestaurantForm, ReservationForm, CustomUserCreationForm

def home(request):
    today = date.today()
    
    # Использование сессий для истории просмотров
    recently_viewed = request.session.get('recently_viewed_restaurants', [])
    recent_restaurants = Restaurant.objects.filter(id__in=recently_viewed)
    
    # Chaining filters и Limiting QuerySets
    week_ago = today - timedelta(days=7)
    popular_restaurants = Restaurant.objects.annotate(
        reservation_count=Count('tables__reservations', 
                              filter=Q(tables__reservations__reservation_date__gte=week_ago))
    ).filter(reservation_count__gt=0).order_by('-reservation_count')[:4]
    
    # Использование кастомного менеджера
    available_tables = Table.available.select_related('restaurant').order_by('-capacity')[:6]
    
    # Цепочка методов с агрегацией
    affordable_restaurants = Restaurant.objects.annotate(
        min_price=Min('tables__price_per_hour')
    ).filter(min_price__isnull=False).order_by('min_price')[:3]
    
    large_tables_restaurants = Restaurant.objects.annotate(
        max_capacity=Max('tables__capacity')
    ).filter(max_capacity__gte=6).order_by('-max_capacity')[:3]
    
    # values() и values_list() для оптимизации
    cuisine_stats = Restaurant.objects.values('cuisine_type').annotate(
        count=Count('id')
    )
    restaurant_ids = Restaurant.objects.values_list('id', flat=True)[:10]
    
    # count() и exists()
    stats = {
        'total_restaurants': Restaurant.objects.count(),
        'has_restaurants': Restaurant.objects.exists(),
        'avg_table_price': Table.objects.aggregate(avg_price=Avg('price_per_hour'))['avg_price'] or 0,
        'max_capacity': Table.objects.aggregate(max_cap=Max('capacity'))['max_cap'] or 0,
        'min_price': Table.objects.aggregate(min_pr=Min('price_per_hour'))['min_pr'] or 0,
    }
    
    # Поиск с __icontains и __contains
    search_results = None
    search_query = ""
    if 'q' in request.GET:
        search_query = request.GET['q']
        search_results = Restaurant.objects.filter(
            Q(name__icontains=search_query) | 
            Q(cuisine_type__icontains=search_query) |
            Q(address__contains=search_query) |
            Q(description__icontains=search_query)
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
        'recent_restaurants': recent_restaurants,
        'cuisine_stats': cuisine_stats,
    }
    return render(request, 'restaurant/home.html', context)

def all_restaurants(request):
    """Пагинация с try/except"""
    restaurant_list = Restaurant.objects.all()
    
    paginator = Paginator(restaurant_list, 6)
    page = request.GET.get('page')
    
    try:
        restaurants = paginator.page(page)
    except PageNotAnInteger:
        restaurants = paginator.page(1)
    except EmptyPage:
        restaurants = paginator.page(paginator.num_pages)
    
    # values() для оптимизации
    restaurant_data = Restaurant.objects.values('id', 'name', 'cuisine_type')[:10]
    
    context = {
        'restaurants': restaurants,
        'restaurant_data': restaurant_data,
    }
    return render(request, 'restaurant/all_restaurants.html', context)

def restaurant_detail(request, restaurant_id):
    # get_object_or_404 автоматически вызывает Http404
    restaurant = get_object_or_404(
        Restaurant.objects.select_related('created_by').prefetch_related('tags', 'tables'), 
        id=restaurant_id
    )
    
    # Сохранение в сессии для истории просмотров
    recently_viewed = request.session.get('recently_viewed_restaurants', [])
    if restaurant_id not in recently_viewed:
        recently_viewed.insert(0, restaurant_id)
        recently_viewed = recently_viewed[:5]
        request.session['recently_viewed_restaurants'] = recently_viewed
    
    # Использование собственного метода модели
    available_tables = restaurant.get_available_tables(timezone.now().date())
    
    # values_list() для оптимизации
    table_ids = restaurant.tables.values_list('id', flat=True)
    
    reservations = Reservation.objects.filter(table__in=table_ids)[:5]
    
    stats = {
        'tables_count': restaurant.tables.count(),
        'tables_exist': restaurant.tables.exists(),
        'avg_capacity': restaurant.tables.aggregate(avg_cap=Avg('capacity'))['avg_cap'] or 0,
        'min_price': restaurant.tables.aggregate(min_pr=Min('price_per_hour'))['min_pr'] or 0,
        'max_capacity': restaurant.tables.aggregate(max_cap=Max('capacity'))['max_cap'] or 0,
    }
    
    context = {
        'restaurant': restaurant,
        'tables': restaurant.tables.all(),
        'available_tables': available_tables,
        'reservations': reservations,
        'stats': stats,
    }
    return render(request, 'restaurant/restaurant_detail.html', context)

@login_required
def restaurant_create(request):
    if not request.user.is_staff:
        messages.error(request, '❌ У вас нет прав для создания ресторанов.')
        return redirect('home')
    
    if request.method == 'POST':
        # request.FILES для загрузки файлов
        form = RestaurantForm(request.POST, request.FILES)
        if form.is_valid():
            # form.cleaned_data доступен после is_valid()
            restaurant = form.save(commit=False)
            restaurant.created_by = request.user
            restaurant.save()
            form.save_m2m()  # Для ManyToMany полей
            
            messages.success(request, f'✅ Ресторан "{restaurant.name}" успешно создан!')
            return redirect('restaurant_detail', restaurant_id=restaurant.id)
        else:
            messages.error(request, '❌ Пожалуйста, исправьте ошибки в форме.')
    else:
        form = RestaurantForm()
    
    context = {
        'form': form,
        'title': 'Добавить ресторан'
    }
    return render(request, 'restaurant/restaurant_form.html', context)

@login_required
def restaurant_edit(request, restaurant_id):
    if not request.user.is_staff:
        messages.error(request, '❌ У вас нет прав для редактирования ресторанов.')
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
    if not request.user.is_staff:
        messages.error(request, '❌ У вас нет прав для удаления ресторанов.')
        return redirect('restaurant_detail', restaurant_id=restaurant_id)
    
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    
    if request.method == 'POST':
        restaurant_name = restaurant.name
        # delete() метод
        restaurant.delete()
        messages.success(request, f'✅ Ресторан "{restaurant_name}" успешно удален!')
        return redirect('all_restaurants')
    
    context = {
        'restaurant': restaurant,
    }
    return render(request, 'restaurant/restaurant_confirm_delete.html', context)

def search_restaurants(request):
    restaurants = None
    query = ""
    
    if 'q' in request.GET:
        query = request.GET['q']
        # __icontains и __contains
        restaurants = Restaurant.objects.filter(
            Q(name__icontains=query) | 
            Q(cuisine_type__icontains=query) |
            Q(address__contains=query) |
            Q(description__icontains=query)
        ).distinct()
    
    if restaurants:
        paginator = Paginator(restaurants, 8)
        page = request.GET.get('page')
        
        try:
            restaurants = paginator.page(page)
        except PageNotAnInteger:
            restaurants = paginator.page(1)
        except EmptyPage:
            restaurants = paginator.page(paginator.num_pages)
    
    search_stats = {}
    if restaurants:
        # values() и annotate
        search_stats = {
            'count': restaurants.paginator.count if hasattr(restaurants, 'paginator') else restaurants.count(),
            'cuisine_types': restaurants.object_list.values('cuisine_type').annotate(count=Count('id')) if hasattr(restaurants, 'object_list') else restaurants.values('cuisine_type').annotate(count=Count('id')),
        }
    
    context = {
        'restaurants': restaurants,
        'query': query,
        'search_stats': search_stats,
    }
    return render(request, 'restaurant/search.html', context)

def register(request):
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
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Добро пожаловать, {username}!')
                
                # Использование сессии
                request.session['user_id'] = user.id
                request.session['login_time'] = timezone.now().isoformat()
                
                next_url = request.GET.get('next', 'home')
                # Альтернатива redirect - HttpResponseRedirect
                return HttpResponseRedirect(next_url)
        else:
            messages.error(request, '❌ Неверное имя пользователя или пароль.')
    else:
        form = AuthenticationForm()
    
    return render(request, 'restaurant/login.html', {'form': form})

def custom_logout(request):
    # Очистка сессии
    if 'user_id' in request.session:
        del request.session['user_id']
    if 'login_time' in request.session:
        del request.session['login_time']
    
    logout(request)
    messages.success(request, 'Вы успешно вышли из системы.')
    return redirect('home')

@login_required
@transaction.atomic
def make_reservation(request, table_id):
    table = get_object_or_404(Table, id=table_id)
    
    if request.method == 'POST':
        form = ReservationForm(request.POST)
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.user = request.user
            reservation.table = table
            
            # exists() для проверки
            conflicting_exists = Reservation.objects.filter(
                table=table,
                reservation_date=reservation.reservation_date,
                reservation_time=reservation.reservation_time,
                status__in=['confirmed', 'pending']
            ).exists()
            
            if conflicting_exists:
                messages.error(request, '❌ Этот столик уже забронирован на выбранное время')
                # Возврат на ту же страницу
                return redirect('make_reservation', table_id=table.id)
            elif reservation.guests_count > table.capacity:
                messages.error(request, f'❌ Столик вмещает только {table.capacity} гостей')
            else:
                reservation.save()
                messages.success(request, f'✅ Столик успешно забронирован на {reservation.reservation_date} в {reservation.reservation_time}')
                return redirect('restaurant_detail', restaurant_id=table.restaurant.id)
    else:
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
    reservations = Reservation.objects.filter(user=request.user).select_related(
        'table', 'table__restaurant'
    ).order_by('-reservation_date', '-reservation_time')
    
    paginator = Paginator(reservations, 10)
    page = request.GET.get('page')
    
    try:
        reservations = paginator.page(page)
    except PageNotAnInteger:
        reservations = paginator.page(1)
    except EmptyPage:
        reservations = paginator.page(paginator.num_pages)
    
    context = {
        'reservations': reservations
    }
    return render(request, 'restaurant/user_reservations.html', context)

@login_required
def cancel_reservation(request, reservation_id):
    # Явный Http404
    try:
        reservation = Reservation.objects.get(id=reservation_id, user=request.user)
    except Reservation.DoesNotExist:
        raise Http404("Бронь не найдена")
    
    if request.method == 'POST':
        # update() для массового обновления
        Reservation.objects.filter(id=reservation_id).update(status='cancelled')
        messages.success(request, '✅ Бронирование отменено')
        return redirect('user_reservations')
    
    context = {
        'reservation': reservation
    }
    return render(request, 'restaurant/cancel_reservation.html', context)

def increase_prices(request, restaurant_id):
    """Демонстрация F expressions"""
    if request.method == 'POST' and request.user.is_staff:
        restaurant = get_object_or_404(Restaurant, id=restaurant_id)
        percentage = float(request.POST.get('percentage', 10))
        
        # Использование F expression для обновления цен
        Table.objects.filter(restaurant=restaurant).update(
            price_per_hour=F('price_per_hour') * (1 + percentage/100)
        )
        
        messages.success(request, f'✅ Цены увеличены на {percentage}%')
        return redirect('restaurant_detail', restaurant_id=restaurant.id)
    
    return redirect('home')

def demo_page(request):
    return render(request, 'restaurant/demo.html')