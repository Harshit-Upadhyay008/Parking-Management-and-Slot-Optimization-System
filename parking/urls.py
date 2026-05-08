from django.urls import path
from . import views

urlpatterns = [
    # Public pages
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),

    # Authentication
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),

    # Parking Map
    path('parking-map/', views.parking_map, name='parking_map'),

    # Bookings
    path('book/', views.book_slot, name='book_slot'),
    path('book/slot/<int:slot_id>/', views.book_specific_slot, name='book_specific_slot'),
    path('booking/<str:booking_id>/', views.booking_detail, name='booking_detail'),
    path('booking/<str:booking_id>/checkout/', views.checkout_booking, name='checkout_booking'),
    path('booking/<str:booking_id>/cancel/', views.cancel_booking, name='cancel_booking'),
    path('bookings/', views.booking_history, name='booking_history'),

    # Vehicles
    path('vehicles/', views.my_vehicles, name='my_vehicles'),
    path('vehicles/add/', views.add_vehicle, name='add_vehicle'),
    path('vehicles/<int:vehicle_id>/edit/', views.edit_vehicle, name='edit_vehicle'),
    path('vehicles/<int:vehicle_id>/delete/', views.delete_vehicle, name='delete_vehicle'),

    # Profile
    path('profile/', views.profile, name='profile'),

    # Admin
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/slots/', views.admin_manage_slots, name='admin_manage_slots'),
    path('admin-panel/slots/<int:slot_id>/toggle/', views.admin_toggle_slot, name='admin_toggle_slot'),
    path('admin-panel/bookings/', views.admin_all_bookings, name='admin_all_bookings'),
    path('admin-panel/messages/', views.admin_messages, name='admin_messages'),
    path('admin-panel/messages/<int:msg_id>/read/', views.admin_mark_message_read, name='admin_mark_message_read'),

    # API
    path('api/availability/', views.api_slot_availability, name='api_slot_availability'),
    path('api/slot/<int:slot_id>/', views.api_slot_info, name='api_slot_info'),
]
