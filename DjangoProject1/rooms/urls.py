from django.urls import path
from . import views

app_name = 'rooms'

urlpatterns = [
    path('', views.room_list, name='room_list'),
    path('room/<int:room_id>/', views.room_detail, name='room_detail'),
    path('reserve/', views.create_reservation, name='create_reservation'),
] 