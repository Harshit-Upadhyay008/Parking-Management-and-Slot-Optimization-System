from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid


class UserProfile(models.Model):
    """Extended user profile with phone and address"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"


class ParkingFloor(models.Model):
    """Represents a floor in the parking building"""
    name = models.CharField(max_length=50)
    floor_number = models.IntegerField(unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['floor_number']

    def __str__(self):
        return f"Floor {self.floor_number} - {self.name}"

    @property
    def total_slots(self):
        return self.slots.count()

    @property
    def available_slots(self):
        return self.slots.filter(status='available').count()

    @property
    def occupied_slots(self):
        return self.slots.filter(status='occupied').count()


class ParkingSlot(models.Model):
    """Individual parking slot"""
    SLOT_TYPES = [
        ('compact', 'Compact'),
        ('regular', 'Regular'),
        ('large', 'Large'),
        ('handicapped', 'Handicapped'),
        ('ev', 'Electric Vehicle'),
    ]
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('occupied', 'Occupied'),
        ('reserved', 'Reserved'),
        ('maintenance', 'Maintenance'),
    ]

    slot_number = models.CharField(max_length=10, unique=True)
    floor = models.ForeignKey(ParkingFloor, on_delete=models.CASCADE, related_name='slots')
    slot_type = models.CharField(max_length=15, choices=SLOT_TYPES, default='regular')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='available')
    hourly_rate = models.DecimalField(max_digits=6, decimal_places=2, default=50.00)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['floor', 'slot_number']

    def __str__(self):
        return f"Slot {self.slot_number} (Floor {self.floor.floor_number})"


class Vehicle(models.Model):
    """User's registered vehicles"""
    VEHICLE_TYPES = [
        ('car', 'Car'),
        ('motorcycle', 'Motorcycle'),
        ('suv', 'SUV'),
        ('truck', 'Truck'),
        ('van', 'Van'),
        ('ev', 'Electric Vehicle'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vehicles')
    license_plate = models.CharField(max_length=20, unique=True)
    vehicle_type = models.CharField(max_length=15, choices=VEHICLE_TYPES, default='car')
    make = models.CharField(max_length=50, help_text="e.g., Toyota, Honda")
    model = models.CharField(max_length=50, help_text="e.g., Corolla, Civic")
    color = models.CharField(max_length=30)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.license_plate} - {self.make} {self.model}"


class Booking(models.Model):
    """Parking booking/reservation"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    ]

    booking_id = models.CharField(max_length=20, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='bookings')
    slot = models.ForeignKey(ParkingSlot, on_delete=models.CASCADE, related_name='bookings')
    check_in = models.DateTimeField()
    check_out = models.DateTimeField(null=True, blank=True)
    expected_hours = models.IntegerField(default=1, help_text="Expected parking duration in hours")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Booking {self.booking_id} - {self.user.username}"

    def save(self, *args, **kwargs):
        if not self.booking_id:
            self.booking_id = f"BK-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    @property
    def total_hours(self):
        if self.check_out:
            delta = self.check_out - self.check_in
            hours = delta.total_seconds() / 3600
            return max(1, round(hours, 1))
        else:
            delta = timezone.now() - self.check_in
            hours = delta.total_seconds() / 3600
            return max(1, round(hours, 1))

    @property
    def total_amount(self):
        return round(float(self.slot.hourly_rate) * self.total_hours, 2)

    @property
    def is_overdue(self):
        if self.status == 'active' and not self.check_out:
            expected_end = self.check_in + timezone.timedelta(hours=self.expected_hours)
            return timezone.now() > expected_end
        return False


class Payment(models.Model):
    """Payment records for bookings"""
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('card', 'Credit/Debit Card'),
        ('online', 'Online Payment'),
        ('wallet', 'Digital Wallet'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    payment_id = models.CharField(max_length=20, unique=True, editable=False)
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='payment')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=15, choices=PAYMENT_METHODS, default='cash')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment {self.payment_id} - Rs.{self.amount}"

    def save(self, *args, **kwargs):
        if not self.payment_id:
            self.payment_id = f"PAY-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)


class ContactMessage(models.Model):
    """Contact form messages"""
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.subject}"
