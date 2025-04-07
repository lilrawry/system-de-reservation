from django.db import models
from django.contrib.auth.models import User

class Room(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nom")
    capacity = models.IntegerField(verbose_name="Capacité")
    description = models.TextField(verbose_name="Description")
    price_per_hour = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix par heure")
    is_available = models.BooleanField(default=True, verbose_name="Disponible")
    image = models.ImageField(upload_to='room_images/', null=True, blank=True, verbose_name="Image")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Salle"
        verbose_name_plural = "Salles"

class Reservation(models.Model):
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('confirmed', 'Confirmée'),
        ('cancelled', 'Annulée')
    ]

    room = models.ForeignKey(Room, on_delete=models.CASCADE, verbose_name="Salle")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Utilisateur")
    start_time = models.DateTimeField(verbose_name="Heure de début")
    end_time = models.DateTimeField(verbose_name="Heure de fin")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créée le")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Statut"
    )
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix total")

    def __str__(self):
        return f"{self.room.name} - {self.user.username} - {self.start_time.date()}"

    class Meta:
        verbose_name = "Réservation"
        verbose_name_plural = "Réservations" 