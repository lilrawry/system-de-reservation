from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Reservation, Room
from django.utils import timezone
import datetime

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ['room', 'start_time', 'end_time']
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['room'].queryset = Room.objects.filter(is_available=True)
        self.fields['room'].empty_label = "Sélectionnez une salle"
        
        # Convert datetime fields to proper format for datetime-local input
        if 'initial' in kwargs and kwargs['initial']:
            if 'start_time' in kwargs['initial']:
                kwargs['initial']['start_time'] = kwargs['initial']['start_time'].strftime('%Y-%m-%dT%H:%M')
            if 'end_time' in kwargs['initial']:
                kwargs['initial']['end_time'] = kwargs['initial']['end_time'].strftime('%Y-%m-%dT%H:%M')

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        room = cleaned_data.get('room')

        if start_time and end_time and room:
            # Convert string inputs to datetime if needed
            if isinstance(start_time, str):
                try:
                    start_time = timezone.make_aware(datetime.datetime.strptime(start_time, '%Y-%m-%dT%H:%M'))
                    cleaned_data['start_time'] = start_time
                except ValueError as e:
                    raise forms.ValidationError("Format de date de début invalide")
            
            if isinstance(end_time, str):
                try:
                    end_time = timezone.make_aware(datetime.datetime.strptime(end_time, '%Y-%m-%dT%H:%M'))
                    cleaned_data['end_time'] = end_time
                except ValueError as e:
                    raise forms.ValidationError("Format de date de fin invalide")

            # Check if start_time is in the past
            if start_time < timezone.now():
                raise forms.ValidationError("Vous ne pouvez pas réserver pour une date passée.")

            if start_time >= end_time:
                raise forms.ValidationError("L'heure de fin doit être postérieure à l'heure de début.")
            
            # Check minimum duration (1 hour)
            duration = (end_time - start_time).total_seconds() / 3600
            if duration < 1:
                raise forms.ValidationError("La durée minimale de réservation est d'une heure.")
            
            # Check if room is available
            existing_reservations = Reservation.objects.filter(
                room=room,
                start_time__lt=end_time,
                end_time__gt=start_time
            ).exclude(status='cancelled')
            
            if existing_reservations.exists():
                raise forms.ValidationError("La salle est déjà réservée pour cette période.")

            # Calculate total price
            cleaned_data['total_price'] = float(room.price_per_hour) * duration

        return cleaned_data 