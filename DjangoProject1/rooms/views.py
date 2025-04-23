from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.http import JsonResponse, HttpResponseServerError
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.utils import timezone
from .models import Room, Reservation
from .forms import ReservationForm, UserRegistrationForm
from datetime import datetime, timedelta
import json
from django.contrib.auth.forms import UserCreationForm
import logging

# Configure logging
logger = logging.getLogger(__name__)

def handler500(request, *args, **argv):
    return render(request, '500.html', status=500)

def register(request):
    try:
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
    except Exception as e:
        logger.error(f"Error in register view: {str(e)}")
        return HttpResponseServerError()

def custom_logout(request):
    try:
        logout(request)
        messages.success(request, 'Vous avez été déconnecté avec succès!')
        if request.path.startswith('/admin/'):
            return redirect('admin_login')
        return redirect('login')
    except Exception as e:
        logger.error(f"Error in custom_logout view: {str(e)}")
        return HttpResponseServerError()

@login_required
def room_list(request):
    try:
        rooms = Room.objects.all()
        
        min_capacity = request.GET.get('min_capacity')
        if min_capacity:
            rooms = rooms.filter(capacity__gte=min_capacity)
        
        max_price = request.GET.get('max_price')
        if max_price:
            rooms = rooms.filter(price_per_hour__lte=max_price)
        
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
    except Exception as e:
        logger.error(f"Error in room_list view: {str(e)}")
        return HttpResponseServerError()

@login_required
def room_detail(request, pk):
    try:
        room = get_object_or_404(Room, pk=pk)
        
        if request.method == 'POST':
            form = ReservationForm(request.POST)
            if form.is_valid():
                reservation = form.save(commit=False)
                reservation.room = room
                reservation.user = request.user
                reservation.total_price = form.cleaned_data['total_price']
                reservation.status = 'confirmed'
                
                try:
                    reservation.save()
                    messages.success(request, 'Réservation effectuée avec succès!')
                    return redirect('rooms:my_reservations')
                except Exception as e:
                    logger.error(f"Error saving reservation: {str(e)}")
                    messages.error(request, 'Une erreur est survenue lors de la réservation.')
        else:
            initial_start = timezone.now().replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
            initial_end = initial_start + timedelta(hours=1)
            form = ReservationForm(initial={'start_time': initial_start, 'end_time': initial_end, 'room': room})
        
        context = {
            'room': room,
            'form': form,
        }
        
        return render(request, 'rooms/room_detail.html', context)
    except Exception as e:
        logger.error(f"Error in room_detail view: {str(e)}")
        return HttpResponseServerError()

@login_required
def create_reservation(request):
    try:
        # Get the room_id from GET parameters when loading the form
        room_id = request.GET.get('room')
        room = None
        if room_id:
            try:
                room = Room.objects.get(pk=room_id)
            except Room.DoesNotExist:
                messages.error(request, "La salle demandée n'existe pas.")
                return redirect('rooms:room_list')
        
        if request.method == 'POST':
            form = ReservationForm(request.POST)
            if form.is_valid():
                try:
                    reservation = form.save(commit=False)
                    reservation.user = request.user
                    reservation.total_price = form.cleaned_data['total_price']
                    reservation.status = 'confirmed'
                    reservation.save()
                    
                    messages.success(request, 'Réservation créée avec succès!')
                    return redirect('rooms:my_reservations')
                except Exception as e:
                    logger.error(f"Error saving reservation: {str(e)}")
                    messages.error(request, 'Une erreur est survenue lors de la création de la réservation.')
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
        else:
            # Pre-fill the form with the selected room and default times
            initial_start = timezone.now().replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
            initial_end = initial_start + timedelta(hours=1)
            initial_data = {
                'start_time': initial_start,
                'end_time': initial_end,
            }
            if room:
                initial_data['room'] = room
            form = ReservationForm(initial=initial_data)
        
        context = {
            'form': form,
            'selected_room': room
        }
        return render(request, 'rooms/create_reservation.html', context)
    except Exception as e:
        logger.error(f"Error in create_reservation view: {str(e)}")
        messages.error(request, "Une erreur inattendue s'est produite. Veuillez réessayer.")
        return redirect('rooms:room_list')

@login_required
def my_reservations(request):
    try:
        reservations = Reservation.objects.filter(user=request.user).order_by('start_time')
        return render(request, 'rooms/my_reservations.html', {'reservations': reservations})
    except Exception as e:
        logger.error(f"Error in my_reservations view: {str(e)}")
        return HttpResponseServerError()

@login_required
def cancel_reservation(request, pk):
    try:
        reservation = get_object_or_404(Reservation, pk=pk, user=request.user)
        if reservation.start_time > timezone.now():
            try:
                reservation.delete()
                messages.success(request, 'Réservation annulée avec succès!')
            except Exception as e:
                logger.error(f"Error deleting reservation: {str(e)}")
                messages.error(request, 'Une erreur est survenue lors de l\'annulation de la réservation.')
        else:
            messages.error(request, 'Impossible d\'annuler une réservation passée.')
        return redirect('rooms:my_reservations')
    except Exception as e:
        logger.error(f"Error in cancel_reservation view: {str(e)}")
        return HttpResponseServerError()

@login_required
def admin_dashboard(request):
    try:
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
    except Exception as e:
        logger.error(f"Error in admin_dashboard view: {str(e)}")
        return HttpResponseServerError()