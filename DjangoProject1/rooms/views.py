from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.http import JsonResponse, HttpResponseServerError, HttpResponse, HttpResponseNotFound
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Room, Reservation, Payment
from .forms import ReservationForm, UserRegistrationForm, PaymentForm
from .utils import generate_reservation_receipt
from django.contrib.auth.models import User, Group
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
import csv
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
import json
from django.contrib.auth.forms import UserCreationForm
import logging
import string
import random
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.conf import settings
import os

# Calculate total price for a reservation
def calculate_total_price(price_per_hour, start_time, end_time):
    """
    Calculate the total price for a reservation based on duration and hourly rate
    """
    duration = (end_time - start_time).total_seconds() / 3600
    return float(price_per_hour) * duration

# Configure logging
logger = logging.getLogger(__name__)

def handler500(request, *args, **argv):
    return render(request, '500.html', status=500)

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

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
        rooms = Room.objects.all().order_by('name')
        
        # Search functionality
        search_query = request.GET.get('search')
        if search_query:
            rooms = rooms.filter(name__icontains=search_query)
        
        min_capacity = request.GET.get('min_capacity')
        if min_capacity:
            try:
                min_capacity = int(min_capacity)
                rooms = rooms.filter(capacity__gte=min_capacity)
            except (ValueError, TypeError):
                messages.error(request, "La capacité minimale doit être un nombre entier.")
        
        max_price = request.GET.get('max_price')
        if max_price:
            try:
                max_price = float(max_price)
                rooms = rooms.filter(price_per_hour__lte=max_price)
            except (ValueError, TypeError):
                messages.error(request, "Le prix maximum doit être un nombre.")
        
        availability = request.GET.get('availability')
        if availability == 'available':
            rooms = rooms.filter(is_available=True)
        elif availability == 'occupied':
            rooms = rooms.filter(is_available=False)
        
        # Pagination
        paginator = Paginator(rooms, 9)  # Show 9 rooms per page
        page = request.GET.get('page')
        try:
            rooms = paginator.page(page)
        except PageNotAnInteger:
            rooms = paginator.page(1)
        except EmptyPage:
            rooms = paginator.page(paginator.num_pages)
        
        context = {
            'rooms': rooms,
            'min_capacity': min_capacity,
            'max_price': max_price,
            'availability': availability,
            'search': search_query,
            'is_paginated': True if rooms.paginator.num_pages > 1 else False,
            'page_obj': rooms,
        }
        
        return render(request, 'rooms/room_list.html', context)
    except Exception as e:
        logger.error(f"Error in room_list view: {str(e)}")
        return HttpResponseServerError("Une erreur s'est produite lors du chargement de la page.")

@login_required
def room_detail(request, pk):
    try:
        room = get_object_or_404(Room, pk=pk)
        min_date_time = timezone.now()
        
        if request.method == 'POST':
            form = ReservationForm(request.POST)
            if form.is_valid():
                reservation = form.save(commit=False)
                reservation.room = room
                reservation.user = request.user
                reservation.total_price = form.cleaned_data['total_price']
                reservation.status = 'pending'
                
                try:
                    reservation.save()
                    messages.success(request, 'Réservation effectuée avec succès!')
                    return redirect('rooms:process_payment', reservation_id=reservation.id)
                except Exception as e:
                    logger.error(f"Error saving reservation: {str(e)}")
                    messages.error(request, 'Une erreur est survenue lors de la réservation.')
        else:
            initial_start = timezone.now().replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
            initial_end = initial_start + timedelta(hours=1)
            form = ReservationForm(initial={'start_time': initial_start, 'end_time': initial_end, 'room': room})
        
        context = {
            'room': room,
            'min_date_time': min_date_time,
            'form': form,
        }
        
        return render(request, 'rooms/room_detail.html', context)
    except Exception as e:
        logger.error(f"Error in room_detail view: {str(e)}")
        return HttpResponseServerError()

@login_required
def create_reservation(request):
    if request.method == 'POST':
        form = ReservationForm(request.POST)
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.user = request.user
            reservation.total_price = calculate_total_price(reservation.room.price_per_hour, 
                                                          reservation.start_time, 
                                                          reservation.end_time)
            reservation.save()
            return redirect('rooms:process_payment', reservation_id=reservation.id)
    else:
        form = ReservationForm()
    return render(request, 'rooms/create_reservation.html', {'form': form})

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
def download_receipt(request, reservation_id):
    try:
        reservation = Reservation.objects.get(id=reservation_id, user=request.user)
        pdf = generate_reservation_receipt(reservation)
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename=reservation_{reservation_id}_receipt.pdf'
        response.write(pdf)
        return response
    except Reservation.DoesNotExist:
        return HttpResponseNotFound('Reservation not found')

@login_required
def download_pdf(request, reservation_id):
    # Get the reservation and ensure the user owns it
    reservation = get_object_or_404(Reservation, pk=reservation_id)
    if reservation.user != request.user and not request.user.is_staff:
        raise Http404("Vous n'êtes pas autorisé à accéder à ce reçu")
    
    # Get the payment associated with this reservation
    try:
        payment = Payment.objects.get(reservation=reservation)
    except Payment.DoesNotExist:
        messages.error(request, "Aucun paiement n'a été trouvé pour cette réservation")
        return redirect('rooms:my_reservations')
    
    if not reservation.is_paid and payment.status != 'completed':
        messages.error(request, "Cette réservation n'a pas encore été payée ou le paiement n'a pas été confirmé.")
        return redirect('rooms:my_reservations')
    
    # Get the template and render it with context
    template = get_template('rooms/receipt_pdf.html')
    logo_url = request.build_absolute_uri(settings.STATIC_URL + 'img/logo.svg')
    
    context = {
        'payment': payment,
        'logo_url': logo_url,
        'today': timezone.now().date(),
    }
    
    html = template.render(context)
    
    # Create the PDF response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="recu_reservation_{reservation.id}.pdf"'
    
    # Generate PDF
    pisa_status = pisa.CreatePDF(html, dest=response)
    
    # Return the response if PDF generated successfully
    if pisa_status.err:
        messages.error(request, "Une erreur est survenue lors de la génération du PDF. Veuillez réessayer.")
        return redirect('rooms:my_reservations')
    
    return response

@login_required
def admin_dashboard(request):
    if not request.user.is_staff:
        messages.error(request, "Accès non autorisé.")
        return redirect('rooms:room_list')
        
    # Get stats for dashboard
    stats = {
        'rooms': Room.objects.count(),
        'reservations': Reservation.objects.count(),
        'users': User.objects.count(),
        'groups': Group.objects.count(),
        'pending_payments': Payment.objects.filter(status='pending').count(),
        'pending_reservations': Reservation.objects.filter(status='pending', is_paid=False).count()
    }
    
    # Get recent payments waiting for approval
    pending_payments = Payment.objects.filter(status='pending').select_related('reservation__user', 'reservation__room').order_by('-payment_date')[:10]
    
    # Get recent reservations waiting for approval
    pending_reservations = Reservation.objects.filter(status='pending', is_paid=False).select_related('user', 'room').order_by('-created_at')[:10]
    
    context = {
        'stats': stats,
        'pending_payments': pending_payments,
        'pending_reservations': pending_reservations,
        'title': 'Tableau de bord administrateur'
    }
    return render(request, 'rooms/admin_dashboard.html', context)

@login_required
def approve_payment(request, payment_id):
    if not request.user.is_staff:
        messages.error(request, "Accès non autorisé.")
        return redirect('rooms:room_list')
    
    payment = get_object_or_404(Payment, id=payment_id)
    
    # Mark the payment as completed
    payment.status = 'completed'
    payment.save()
    
    # Update the reservation status
    reservation = payment.reservation
    reservation.status = 'confirmed'
    reservation.is_paid = True
    reservation.save()
    
    messages.success(request, f"Paiement #{payment_id} approuvé avec succès. La réservation est confirmée.")
    return redirect('rooms:admin_dashboard')

@login_required
def reject_payment(request, payment_id):
    if not request.user.is_staff:
        messages.error(request, "Accès non autorisé.")
        return redirect('rooms:room_list')
    
    payment = get_object_or_404(Payment, id=payment_id)
    
    # Mark the payment as failed
    payment.status = 'failed'
    payment.save()
    
    messages.success(request, f"Paiement #{payment_id} rejeté. La réservation reste en attente.")
    return redirect('rooms:admin_dashboard')

@login_required
def approve_reservation(request, reservation_id):
    if not request.user.is_staff:
        messages.error(request, "Accès non autorisé.")
        return redirect('rooms:room_list')
    
    reservation = get_object_or_404(Reservation, id=reservation_id)
    
    # Mark the reservation as confirmed
    reservation.status = 'confirmed'
    reservation.save()
    
    messages.success(request, f"Réservation #{reservation_id} approuvée avec succès.")
    return redirect('rooms:admin_dashboard')

@login_required
def reject_reservation(request, reservation_id):
    if not request.user.is_staff:
        messages.error(request, "Accès non autorisé.")
        return redirect('rooms:room_list')
    
    reservation = get_object_or_404(Reservation, id=reservation_id)
    
    # Mark the reservation as cancelled
    reservation.status = 'cancelled'
    reservation.save()
    
    messages.success(request, f"Réservation #{reservation_id} rejetée.")
    return redirect('rooms:admin_dashboard')

@login_required
def export_rooms_csv(request):
    if not request.user.is_staff:
        messages.error(request, "Accès non autorisé.")
        return redirect('rooms:room_list')

    # Get filter parameters
    available_only = request.GET.get('available') == '1'
    min_capacity = request.GET.get('min_capacity')
    max_price = request.GET.get('max_price')

    # Base queryset
    rooms = Room.objects.all().order_by('name')
    
    # Apply filters
    if available_only:
        rooms = rooms.filter(is_available=True)
    if min_capacity:
        try:
            rooms = rooms.filter(capacity__gte=int(min_capacity))
        except ValueError:
            pass
    if max_price:
        try:
            rooms = rooms.filter(price_per_hour__lte=float(max_price))
        except ValueError:
            pass

    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    filename = 'salles'
    if available_only:
        filename += '_disponibles'
    if min_capacity:
        filename += f'_min{min_capacity}pers'
    if max_price:
        filename += f'_max{max_price}eur'
    response['Content-Disposition'] = f'attachment; filename={filename}_{timezone.now().strftime("%Y%m%d_%H%M")}.csv'
    
    writer = csv.writer(response, delimiter=';')
    writer.writerow([
        'Nom de la salle',
        'Capacité (personnes)',
        'Prix par heure (€)',
        'Disponible',
        'Description',
        'Nombre de réservations',
        'Dernière réservation',
        'Revenu total (€)',
        'Date de création',
        'Dernière modification'
    ])
    
    for room in rooms:
        # Get room statistics
        reservations = room.reservation_set.all()
        last_reservation = reservations.order_by('-start_time').first()
        total_revenue = sum(r.total_price for r in reservations)
        
        writer.writerow([
            room.name,
            room.capacity,
            f"{room.price_per_hour:.2f}",
            'Oui' if room.is_available else 'Non',
            room.description or '',
            reservations.count(),
            timezone.localtime(last_reservation.start_time).strftime('%d/%m/%Y %H:%M') if last_reservation else 'Jamais',
            f"{total_revenue:.2f}",
            timezone.localtime(room.created_at).strftime('%d/%m/%Y %H:%M') if hasattr(room, 'created_at') else '',
            timezone.localtime(room.updated_at).strftime('%d/%m/%Y %H:%M') if hasattr(room, 'updated_at') else ''
        ])
    
    return response

@login_required
def export_reservations_csv(request):
    if not request.user.is_staff:
        messages.error(request, "Accès non autorisé.")
        return redirect('rooms:room_list')

    # Get filter parameters
    status = request.GET.get('status')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    room_id = request.GET.get('room')

    # Base queryset with related fields
    reservations = Reservation.objects.all().select_related('room', 'user').order_by('-start_time')
    
    # Apply filters
    if status:
        reservations = reservations.filter(status=status)
    if start_date:
        try:
            start = timezone.make_aware(datetime.strptime(start_date, '%Y-%m-%d'))
            reservations = reservations.filter(start_time__gte=start)
        except ValueError:
            pass
    if end_date:
        try:
            end = timezone.make_aware(datetime.strptime(end_date, '%Y-%m-%d'))
            reservations = reservations.filter(end_time__lte=end)
        except ValueError:
            pass
    if room_id:
        try:
            reservations = reservations.filter(room_id=int(room_id))
        except ValueError:
            pass

    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    filename = 'reservations'
    if status:
        filename += f'_{status}'
    if start_date:
        filename += f'_depuis{start_date}'
    if end_date:
        filename += f'_jusqua{end_date}'
    if room_id:
        try:
            room = Room.objects.get(id=int(room_id))
            filename += f'_{room.name}'
        except (Room.DoesNotExist, ValueError):
            pass
            
    response['Content-Disposition'] = f'attachment; filename={filename}_{timezone.now().strftime("%Y%m%d_%H%M")}.csv'
    
    writer = csv.writer(response, delimiter=';')
    writer.writerow([
        'Salle',
        'Utilisateur',
        'Email',
        'Date de début',
        'Date de fin',
        'Durée (heures)',
        'Prix total (€)',
        'Prix par heure (€)',
        'Statut',
        'Mode de paiement',
        'Date de réservation',
        'Date d\'annulation',
        'Motif d\'annulation'
    ])
    
    for res in reservations:
        duration = (res.end_time - res.start_time).total_seconds() / 3600
        writer.writerow([
            res.room.name,
            f"{res.user.first_name} {res.user.last_name}" if res.user.first_name else res.user.username,
            res.user.email,
            timezone.localtime(res.start_time).strftime('%d/%m/%Y %H:%M'),
            timezone.localtime(res.end_time).strftime('%d/%m/%Y %H:%M'),
            f"{duration:.1f}",
            f"{res.total_price:.2f}",
            f"{res.room.price_per_hour:.2f}",
            dict(Reservation.STATUS_CHOICES).get(res.status, res.status),
            getattr(res, 'payment_method', 'Non spécifié'),
            timezone.localtime(res.created_at).strftime('%d/%m/%Y %H:%M') if hasattr(res, 'created_at') else '',
            timezone.localtime(res.cancelled_at).strftime('%d/%m/%Y %H:%M') if hasattr(res, 'cancelled_at') and res.cancelled_at else '',
            getattr(res, 'cancellation_reason', '') if res.status == 'cancelled' else ''
        ])
    
    return response

@login_required
def import_rooms_csv(request):
    if not request.user.is_staff:
        messages.error(request, "Accès non autorisé.")
        return redirect('rooms:room_list')

    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        
        if not csv_file.name.endswith('.csv'):
            messages.error(request, "Le fichier doit être au format CSV.")
            return redirect('rooms:admin_dashboard')
            
        try:
            decoded_file = csv_file.read().decode('utf-8-sig').splitlines()
            reader = csv.DictReader(decoded_file, delimiter=';')
            
            required_fields = ['Nom de la salle', 'Capacité (personnes)', 'Prix par heure (€)']
            if not all(field in reader.fieldnames for field in required_fields):
                messages.error(request, "Le fichier CSV ne contient pas toutes les colonnes requises.")
                return redirect('rooms:admin_dashboard')
            
            success_count = 0
            error_count = 0
            update_count = 0
            error_details = []
            
            for row_num, row in enumerate(reader, start=1):
                try:
                    # Validate row data
                    row_errors = validate_csv_content(row)
                    if row_errors:
                        error_count += 1
                        error_details.extend(f"Ligne {row_num}: {error}" for error in row_errors)
                        continue
                        
                    name = row['Nom de la salle'].strip()
                    capacity = int(row['Capacité (personnes)'].strip())
                    price = float(row['Prix par heure (€)'].strip().replace(',', '.'))
                    is_available = row.get('Disponible', '').strip().lower()
                    is_available = is_available in ['oui', 'yes', 'true', '1']
                    description = row.get('Description', '').strip()
                    
                    # Create or update room
                    room, created = Room.objects.update_or_create(
                        name=name,
                        defaults={
                            'capacity': capacity,
                            'price_per_hour': price,
                            'is_available': is_available,
                            'description': description
                        }
                    )
                    
                    if created:
                        success_count += 1
                    else:
                        update_count += 1
                    
                except Exception as e:
                    error_count += 1
                    error_details.append(f"Ligne {row_num}: {str(e)}")
                    continue
            
            # Show detailed results
            if success_count > 0:
                messages.success(request, f"{success_count} nouvelle(s) salle(s) créée(s)")
            if update_count > 0:
                messages.info(request, f"{update_count} salle(s) mise(s) à jour")
            if error_count > 0:
                messages.warning(request, f"{error_count} erreur(s) lors de l'import")
                for error in error_details[:5]:  # Show first 5 errors
                    messages.error(request, error)
                if len(error_details) > 5:
                    messages.error(request, f"... et {len(error_details) - 5} autre(s) erreur(s)")
                
        except Exception as e:
            messages.error(request, f"Erreur lors de l'import: {str(e)}")
            
    return redirect('rooms:admin_dashboard')

def validate_csv_content(row):
    """Validate CSV row data"""
    errors = []
    
    # Validate name
    name = row.get('Nom de la salle', '').strip()
    if not name:
        errors.append("Le nom de la salle est obligatoire")
    elif len(name) > 100:
        errors.append("Le nom de la salle est trop long (max 100 caractères)")
    
    # Validate capacity
    try:
        capacity = int(row.get('Capacité (personnes)', '0').strip())
        if capacity <= 0:
            errors.append("La capacité doit être supérieure à 0")
        elif capacity > 1000:
            errors.append("La capacité ne peut pas dépasser 1000 personnes")
    except ValueError:
        errors.append("La capacité doit être un nombre entier")
    
    # Validate price
    try:
        price = float(row.get('Prix par heure (€)', '0').strip().replace(',', '.'))
        if price < 0:
            errors.append("Le prix ne peut pas être négatif")
        elif price > 10000:
            errors.append("Le prix ne peut pas dépasser 10000€")
    except ValueError:
        errors.append("Le prix doit être un nombre")
    
    return errors

@login_required
def preview_csv_import(request):
    if not request.user.is_staff:
        return JsonResponse({'error': 'Accès non autorisé'}, status=403)
        
    if request.method != 'POST' or 'csv_file' not in request.FILES:
        return JsonResponse({'error': 'Fichier CSV requis'}, status=400)
        
    csv_file = request.FILES['csv_file']
    if not csv_file.name.endswith('.csv'):
        return JsonResponse({'error': 'Le fichier doit être au format CSV'}, status=400)
        
    try:
        decoded_file = csv_file.read().decode('utf-8-sig').splitlines()
        reader = csv.DictReader(decoded_file, delimiter=';')
        
        required_fields = ['Nom de la salle', 'Capacité (personnes)', 'Prix par heure (€)']
        if not all(field in reader.fieldnames for field in required_fields):
            return JsonResponse({
                'error': 'Colonnes manquantes',
                'required': required_fields,
                'found': reader.fieldnames
            }, status=400)
        
        preview_data = []
        all_errors = []
        row_count = 0
        
        for row in reader:
            row_count += 1
            if row_count > 5:  # Only preview first 5 rows
                break
                
            row_errors = validate_csv_content(row)
            preview_data.append({
                'data': row,
                'errors': row_errors
            })
            if row_errors:
                all_errors.extend(f"Ligne {row_count}: {error}" for error in row_errors)
        
        return JsonResponse({
            'preview': preview_data,
            'total_rows': sum(1 for row in csv.DictReader(decoded_file, delimiter=';')),
            'errors': all_errors,
            'fieldnames': reader.fieldnames
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def process_payment(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id, user=request.user)
    
    if reservation.is_paid:
        messages.info(request, 'Cette réservation a déjà été payée.')
        return redirect('rooms:my_reservations')
        
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.reservation = reservation
            payment.amount = reservation.total_price
            # Generate a unique transaction ID
            payment.transaction_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
            payment.status = 'pending'  # In a real system, this would be handled by a payment gateway
            payment.save()
            
            messages.success(request, 'Paiement effectué avec succès!')
            return redirect('rooms:my_reservations')
    else:
        form = PaymentForm()
        
    return render(request, 'rooms/process_payment.html', {
        'reservation': reservation,
        'form': form
    })