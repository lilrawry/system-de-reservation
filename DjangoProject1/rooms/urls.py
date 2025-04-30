from django.urls import path
from . import views

app_name = 'rooms'

urlpatterns = [
    path('', views.room_list, name='room_list'),
    path('room/<int:pk>/', views.room_detail, name='room_detail'),
    path('reserve/', views.create_reservation, name='create_reservation'),
    path('my-reservations/', views.my_reservations, name='my_reservations'),
    path('reservation/<int:pk>/cancel/', views.cancel_reservation, name='cancel_reservation'),
    path('reservation/<int:reservation_id>/pdf/', views.download_pdf, name='download_pdf'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('export-rooms-csv/', views.export_rooms_csv, name='export_rooms_csv'),
    path('export-reservations-csv/', views.export_reservations_csv, name='export_reservations_csv'),
    path('import-rooms-csv/', views.import_rooms_csv, name='import_rooms_csv'),
    path('preview-csv-import/', views.preview_csv_import, name='preview_csv_import'),
    path('reservation/<int:reservation_id>/payment/', views.process_payment, name='process_payment'),
    path('payment/<int:payment_id>/approve/', views.approve_payment, name='approve_payment'),
    path('payment/<int:payment_id>/reject/', views.reject_payment, name='reject_payment'),
    path('reservation/<int:reservation_id>/approve/', views.approve_reservation, name='approve_reservation'),
    path('reservation/<int:reservation_id>/reject/', views.reject_reservation, name='reject_reservation'),
]
