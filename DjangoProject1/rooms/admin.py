from django.contrib import admin
from .models import Room, Reservation

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'capacity', 'price_per_hour', 'is_available')
    list_filter = ('is_available',)
    search_fields = ('name', 'description')
    
    def get_list_display(self, request):
        return ('name', 'capacity', 'price_per_hour', 'is_available')
    
    def get_list_display_links(self, request):
        return ('name',)

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('room', 'user', 'start_time', 'end_time', 'status', 'total_price')
    list_filter = ('status',)
    search_fields = ('room__name', 'user__username')
    
    def get_list_display(self, request):
        return ('room', 'user', 'start_time', 'end_time', 'status', 'total_price')
    
    def get_list_display_links(self, request):
        return ('room', 'user') 