from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Room, Reservation
from datetime import datetime
import json

def room_list(request):
    rooms = Room.objects.filter(is_available=True)
    return render(request, 'rooms/room_list.html', {'rooms': rooms})

@login_required
def room_detail(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    return render(request, 'rooms/room_detail.html', {'room': room})

@login_required
@require_POST
def create_reservation(request):
    data = json.loads(request.body)
    room_id = data.get('room_id')
    start_time = datetime.fromisoformat(data.get('start_time'))
    end_time = datetime.fromisoformat(data.get('end_time'))
    
    room = get_object_or_404(Room, id=room_id)
    
    # Vérifier si la salle est disponible pour la période sélectionnée
    existing_reservations = Reservation.objects.filter(
        room=room,
        start_time__lt=end_time,
        end_time__gt=start_time,
        status='confirmed'
    )
    
    if existing_reservations.exists():
        return JsonResponse({
            'status': 'error',
            'message': 'La salle est déjà réservée pour cette période'
        }, status=400)
    
    # Calculer le prix total
    hours = (end_time - start_time).total_seconds() / 3600
    total_price = room.price_per_hour * hours
    
    reservation = Reservation.objects.create(
        room=room,
        user=request.user,
        start_time=start_time,
        end_time=end_time,
        total_price=total_price
    )
    
    return JsonResponse({
        'status': 'success',
        'reservation_id': reservation.id
    }) 