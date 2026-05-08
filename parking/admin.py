from django.contrib import admin
from .models import UserProfile, ParkingFloor, ParkingSlot, Vehicle, Booking, Payment, ContactMessage


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'created_at']
    search_fields = ['user__username', 'phone']


@admin.register(ParkingFloor)
class ParkingFloorAdmin(admin.ModelAdmin):
    list_display = ['name', 'floor_number', 'total_slots', 'available_slots', 'is_active']
    list_filter = ['is_active']


@admin.register(ParkingSlot)
class ParkingSlotAdmin(admin.ModelAdmin):
    list_display = ['slot_number', 'floor', 'slot_type', 'status', 'hourly_rate', 'is_active']
    list_filter = ['status', 'slot_type', 'floor', 'is_active']
    search_fields = ['slot_number']


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ['license_plate', 'vehicle_type', 'make', 'model', 'color', 'user']
    list_filter = ['vehicle_type']
    search_fields = ['license_plate', 'make', 'model']


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['booking_id', 'user', 'vehicle', 'slot', 'check_in', 'check_out', 'status']
    list_filter = ['status', 'created_at']
    search_fields = ['booking_id', 'user__username']
    readonly_fields = ['booking_id']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['payment_id', 'booking', 'amount', 'payment_method', 'status', 'paid_at']
    list_filter = ['status', 'payment_method']
    search_fields = ['payment_id']
    readonly_fields = ['payment_id']


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'subject', 'is_read', 'created_at']
    list_filter = ['is_read']
    search_fields = ['name', 'email', 'subject']
