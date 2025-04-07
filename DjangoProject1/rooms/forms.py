from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Reservation, Room

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

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        room = cleaned_data.get('room')

        if start_time and end_time and room:
            if start_time >= end_time:
                raise forms.ValidationError("L'heure de fin doit être postérieure à l'heure de début.")
            
            # Vérifier si la salle est disponible pour la période sélectionnée
            existing_reservations = Reservation.objects.filter(
                room=room,
                start_time__lt=end_time,
                end_time__gt=start_time
            )
            
            if existing_reservations.exists():
                raise forms.ValidationError("La salle est déjà réservée pour cette période.")

        return cleaned_data 