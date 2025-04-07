from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.utils import timezone
from .models import Room, Reservation
from .forms import ReservationForm, UserRegistrationForm
from datetime import datetime, timedelta
import json
from django.contrib.auth.forms import UserCreationForm

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Compte créé avec succès! Bienvenue.')
            return redirect('rooms:room_list')
        else:
            messages.error(request, 'Erreur lors de la création du compte. Veuillez corriger les erreurs ci-dessous.')
    else:
        form = UserCreationForm()
    
    return render(request, 'registration/register.html', {'form': form})

def custom_logout(request):
    logout(request)
    messages.success(request, 'Vous avez été déconnecté avec succès!')
    return redirect('rooms:room_list')

@login_required
def room_list(request):
    rooms = Room.objects.all()
    
    # Filter by capacity
    min_capacity = request.GET.get('min_capacity')
    if min_capacity:
        rooms = rooms.filter(capacity__gte=min_capacity)
    
    # Filter by price
    max_price = request.GET.get('max_price')
    if max_price:
        rooms = rooms.filter(price_per_hour__lte=max_price)
    
    # Filter by availability
    available_only = request.GET.get('available_only')
    if available_only:
        rooms = rooms.filter(is_available=True)
    
    context = {
        'rooms': rooms,
        'min_capacity': min_capacity,
        'max_price': max_price,
        'available_only': available_only,
    }
    
    return render(request, 'rooms/room_list.html', context)

@login_required
def room_detail(request, pk):
    room = get_object_or_404(Room, pk=pk)
    
    if request.method == 'POST':
        form = ReservationForm(request.POST)
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.room = room
            reservation.user = request.user
            
            # Check if the room is available for the selected time
            start_time = form.cleaned_data['start_time']
            end_time = form.cleaned_data['end_time']
            
            # Check for conflicts with existing reservations
            conflicts = Reservation.objects.filter(
                room=room,
                start_time__lt=end_time,
                end_time__gt=start_time
            )
            
            if conflicts.exists():
                messages.error(request, 'Cette salle est déjà réservée pour cette période.')
            else:
                reservation.save()
                messages.success(request, 'Réservation effectuée avec succès!')
                return redirect('rooms:room_list')
    else:
        form = ReservationForm()
    
    context = {
        'room': room,
        'form': form,
    }
    
    return render(request, 'rooms/room_detail.html', context)

@login_required
@require_POST
def create_reservation(request):
    if request.method == 'POST':
        form = ReservationForm(request.POST)
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.user = request.user
            
            # Calculer le prix total
            duration = (reservation.end_time - reservation.start_time).total_seconds() / 3600
            reservation.total_price = reservation.room.price_per_hour * duration
            
            reservation.save()
            messages.success(request, 'Réservation créée avec succès!')
            return redirect('rooms:my_reservations')
    else:
        form = ReservationForm()
    return render(request, 'rooms/create_reservation.html', {'form': form})

@login_required
def my_reservations(request):
    reservations = Reservation.objects.filter(user=request.user).order_by('start_time')
    return render(request, 'rooms/my_reservations.html', {'reservations': reservations})

@login_required
def cancel_reservation(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk, user=request.user)
    if reservation.start_time > timezone.now():
        reservation.delete()
        messages.success(request, 'Réservation annulée avec succès!')
    else:
        messages.error(request, 'Impossible d\'annuler une réservation passée.')
    return redirect('rooms:my_reservations')

@login_required
def admin_dashboard(request):
    if not request.user.is_staff:
        messages.error(request, 'Accès non autorisé.')
        return redirect('rooms:room_list')
        
    rooms = Room.objects.all()
    reservations = Reservation.objects.all().order_by('-start_time')
    total_rooms = rooms.count()
    total_reservations = reservations.count()
    active_reservations = reservations.filter(end_time__gt=timezone.now()).count()
    
    context = {
        'rooms': rooms,
        'reservations': reservations,
        'total_rooms': total_rooms,
        'total_reservations': total_reservations,
        'active_reservations': active_reservations,
    }
    return render(request, 'rooms/admin_dashboard.html', context) 