from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Count, Q
from django.http import JsonResponse

from .models import (
    UserProfile, ParkingFloor, ParkingSlot, Vehicle,
    Booking, Payment, ContactMessage
)
from .forms import (
    UserRegistrationForm, LoginForm, VehicleForm,
    BookingForm, ContactForm
)


# ========================
# PUBLIC VIEWS
# ========================

def home(request):
    """Landing page"""
    total_slots = ParkingSlot.objects.filter(is_active=True).count()
    available_slots = ParkingSlot.objects.filter(status='available', is_active=True).count()
    total_users = UserProfile.objects.count()
    total_bookings = Booking.objects.count()

    context = {
        'total_slots': total_slots,
        'available_slots': available_slots,
        'total_users': total_users,
        'total_bookings': total_bookings,
    }
    return render(request, 'parking/home.html', context)


def about(request):
    """About page"""
    return render(request, 'parking/about.html')


def contact(request):
    """Contact page"""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your message has been sent successfully!')
            return redirect('contact')
    else:
        form = ContactForm()
    return render(request, 'parking/contact.html', {'form': form})


# ========================
# AUTHENTICATION VIEWS
# ========================

def register_view(request):
    """User registration"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create user profile
            UserProfile.objects.create(
                user=user,
                phone=form.cleaned_data.get('phone', '')
            )
            login(request, user)
            messages.success(request, f'Welcome {user.first_name}! Your account has been created.')
            return redirect('dashboard')
    else:
        form = UserRegistrationForm()
    return render(request, 'parking/register.html', {'form': form})


def login_view(request):
    """User login"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.first_name or user.username}!')
                next_url = request.GET.get('next', 'dashboard')
                return redirect(next_url)
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()
    return render(request, 'parking/login.html', {'form': form})


def logout_view(request):
    """User logout"""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('home')


# ========================
# DASHBOARD VIEWS
# ========================

@login_required
def dashboard(request):
    """User dashboard"""
    user = request.user
    active_bookings = Booking.objects.filter(user=user, status='active')
    recent_bookings = Booking.objects.filter(user=user)[:5]
    vehicles = Vehicle.objects.filter(user=user)
    total_spent = Payment.objects.filter(
        booking__user=user, status='completed'
    ).aggregate(total=Sum('amount'))['total'] or 0

    # Parking overview
    total_slots = ParkingSlot.objects.filter(is_active=True).count()
    available_slots = ParkingSlot.objects.filter(status='available', is_active=True).count()
    floors = ParkingFloor.objects.filter(is_active=True)

    context = {
        'active_bookings': active_bookings,
        'recent_bookings': recent_bookings,
        'vehicles': vehicles,
        'total_spent': total_spent,
        'total_slots': total_slots,
        'available_slots': available_slots,
        'floors': floors,
        'active_count': active_bookings.count(),
        'total_bookings': Booking.objects.filter(user=user).count(),
        'vehicle_count': vehicles.count(),
    }
    return render(request, 'parking/dashboard.html', context)


# ========================
# PARKING MAP VIEW
# ========================

@login_required
def parking_map(request):
    """Visual parking map showing all floors and slots"""
    floors = ParkingFloor.objects.filter(is_active=True).prefetch_related('slots')
    total_slots = ParkingSlot.objects.filter(is_active=True).count()
    available_slots = ParkingSlot.objects.filter(status='available', is_active=True).count()

    context = {
        'floors': floors,
        'total_slots': total_slots,
        'available_slots': available_slots,
    }
    return render(request, 'parking/parking_map.html', context)


# ========================
# BOOKING VIEWS
# ========================

@login_required
def book_slot(request):
    """Book a parking slot"""
    if request.method == 'POST':
        form = BookingForm(request.user, request.POST)
        if form.is_valid():
            vehicle = form.cleaned_data['vehicle']
            slot = form.cleaned_data['slot']
            expected_hours = form.cleaned_data['expected_hours']

            # Check if slot is still available
            slot.refresh_from_db()
            if slot.status != 'available':
                messages.error(request, 'Sorry, this slot is no longer available.')
                return redirect('book_slot')

            # Create booking
            booking = Booking.objects.create(
                user=request.user,
                vehicle=vehicle,
                slot=slot,
                check_in=timezone.now(),
                expected_hours=expected_hours,
                status='active'
            )

            # Update slot status
            slot.status = 'occupied'
            slot.save()

            # Create pending payment
            amount = float(slot.hourly_rate) * expected_hours
            Payment.objects.create(
                booking=booking,
                amount=amount,
                status='pending'
            )

            messages.success(
                request,
                f'Booking confirmed! Your booking ID is {booking.booking_id}. '
                f'Slot: {slot.slot_number}, Duration: {expected_hours} hours.'
            )
            return redirect('booking_detail', booking_id=booking.booking_id)
    else:
        form = BookingForm(request.user)

    available_slots = ParkingSlot.objects.filter(
        status='available', is_active=True
    ).select_related('floor')

    context = {
        'form': form,
        'available_slots': available_slots,
    }
    return render(request, 'parking/book_slot.html', context)


@login_required
def book_specific_slot(request, slot_id):
    """Book a specific parking slot from the map"""
    slot = get_object_or_404(ParkingSlot, id=slot_id, status='available', is_active=True)
    vehicles = Vehicle.objects.filter(user=request.user)

    if not vehicles.exists():
        messages.warning(request, 'Please add a vehicle first before booking.')
        return redirect('add_vehicle')

    if request.method == 'POST':
        vehicle_id = request.POST.get('vehicle')
        expected_hours = int(request.POST.get('expected_hours', 1))
        vehicle = get_object_or_404(Vehicle, id=vehicle_id, user=request.user)

        # Check availability again
        slot.refresh_from_db()
        if slot.status != 'available':
            messages.error(request, 'Sorry, this slot is no longer available.')
            return redirect('parking_map')

        # Create booking
        booking = Booking.objects.create(
            user=request.user,
            vehicle=vehicle,
            slot=slot,
            check_in=timezone.now(),
            expected_hours=expected_hours,
            status='active'
        )

        slot.status = 'occupied'
        slot.save()

        amount = float(slot.hourly_rate) * expected_hours
        Payment.objects.create(booking=booking, amount=amount, status='pending')

        messages.success(request, f'Booking confirmed! ID: {booking.booking_id}')
        return redirect('booking_detail', booking_id=booking.booking_id)

    context = {
        'slot': slot,
        'vehicles': vehicles,
    }
    return render(request, 'parking/book_specific_slot.html', context)


@login_required
def booking_detail(request, booking_id):
    """View booking details"""
    booking = get_object_or_404(Booking, booking_id=booking_id, user=request.user)
    payment = Payment.objects.filter(booking=booking).first()

    context = {
        'booking': booking,
        'payment': payment,
    }
    return render(request, 'parking/booking_detail.html', context)


@login_required
def checkout_booking(request, booking_id):
    """Check out from a parking slot"""
    booking = get_object_or_404(Booking, booking_id=booking_id, user=request.user, status='active')

    if request.method == 'POST':
        payment_method = request.POST.get('payment_method', 'cash')

        # Complete the booking
        booking.check_out = timezone.now()
        booking.status = 'completed'
        booking.save()

        # Free the slot
        booking.slot.status = 'available'
        booking.slot.save()

        # Update payment
        payment = Payment.objects.filter(booking=booking).first()
        if payment:
            payment.amount = booking.total_amount
            payment.payment_method = payment_method
            payment.status = 'completed'
            payment.paid_at = timezone.now()
            payment.save()

        messages.success(
            request,
            f'Checkout complete! Total: Rs.{booking.total_amount}. '
            f'Thank you for using Smart Parking System.'
        )
        return redirect('booking_detail', booking_id=booking.booking_id)

    context = {'booking': booking}
    return render(request, 'parking/checkout.html', context)


@login_required
def cancel_booking(request, booking_id):
    """Cancel a booking"""
    booking = get_object_or_404(Booking, booking_id=booking_id, user=request.user, status='active')

    if request.method == 'POST':
        booking.status = 'cancelled'
        booking.check_out = timezone.now()
        booking.save()

        # Free the slot
        booking.slot.status = 'available'
        booking.slot.save()

        # Update payment
        payment = Payment.objects.filter(booking=booking).first()
        if payment:
            payment.status = 'refunded'
            payment.save()

        messages.success(request, f'Booking {booking.booking_id} has been cancelled.')
        return redirect('booking_history')

    return render(request, 'parking/cancel_booking.html', {'booking': booking})


@login_required
def booking_history(request):
    """View all bookings"""
    bookings = Booking.objects.filter(user=request.user).select_related(
        'vehicle', 'slot', 'slot__floor', 'payment'
    )

    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        bookings = bookings.filter(status=status_filter)

    context = {
        'bookings': bookings,
        'status_filter': status_filter,
    }
    return render(request, 'parking/booking_history.html', context)


# ========================
# VEHICLE VIEWS
# ========================

@login_required
def my_vehicles(request):
    """List user's vehicles"""
    vehicles = Vehicle.objects.filter(user=request.user)
    return render(request, 'parking/my_vehicles.html', {'vehicles': vehicles})


@login_required
def add_vehicle(request):
    """Add a new vehicle"""
    if request.method == 'POST':
        form = VehicleForm(request.POST)
        if form.is_valid():
            vehicle = form.save(commit=False)
            vehicle.user = request.user
            vehicle.save()
            messages.success(request, f'Vehicle {vehicle.license_plate} added successfully!')
            return redirect('my_vehicles')
    else:
        form = VehicleForm()
    return render(request, 'parking/add_vehicle.html', {'form': form})


@login_required
def edit_vehicle(request, vehicle_id):
    """Edit a vehicle"""
    vehicle = get_object_or_404(Vehicle, id=vehicle_id, user=request.user)
    if request.method == 'POST':
        form = VehicleForm(request.POST, instance=vehicle)
        if form.is_valid():
            form.save()
            messages.success(request, 'Vehicle updated successfully!')
            return redirect('my_vehicles')
    else:
        form = VehicleForm(instance=vehicle)
    return render(request, 'parking/edit_vehicle.html', {'form': form, 'vehicle': vehicle})


@login_required
def delete_vehicle(request, vehicle_id):
    """Delete a vehicle"""
    vehicle = get_object_or_404(Vehicle, id=vehicle_id, user=request.user)
    if request.method == 'POST':
        # Check if vehicle has active bookings
        active_bookings = Booking.objects.filter(vehicle=vehicle, status='active').exists()
        if active_bookings:
            messages.error(request, 'Cannot delete vehicle with active bookings.')
            return redirect('my_vehicles')
        vehicle.delete()
        messages.success(request, 'Vehicle deleted successfully!')
        return redirect('my_vehicles')
    return render(request, 'parking/delete_vehicle.html', {'vehicle': vehicle})


# ========================
# PROFILE VIEW
# ========================

@login_required
def profile(request):
    """User profile page"""
    user = request.user
    profile_obj, _ = UserProfile.objects.get_or_create(user=user)

    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.save()

        profile_obj.phone = request.POST.get('phone', '')
        profile_obj.address = request.POST.get('address', '')
        profile_obj.save()

        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')

    context = {
        'profile': profile_obj,
    }
    return render(request, 'parking/profile.html', context)


# ========================
# ADMIN DASHBOARD VIEWS
# ========================

@login_required
def admin_dashboard(request):
    """Admin dashboard with analytics"""
    if not request.user.is_staff:
        messages.error(request, 'Access denied. Admin only.')
        return redirect('dashboard')

    # Statistics
    total_slots = ParkingSlot.objects.filter(is_active=True).count()
    available_slots = ParkingSlot.objects.filter(status='available', is_active=True).count()
    occupied_slots = ParkingSlot.objects.filter(status='occupied', is_active=True).count()
    total_users = UserProfile.objects.count()
    total_bookings = Booking.objects.count()
    active_bookings = Booking.objects.filter(status='active').count()
    total_revenue = Payment.objects.filter(status='completed').aggregate(
        total=Sum('amount')
    )['total'] or 0

    # Recent bookings
    recent_bookings = Booking.objects.select_related(
        'user', 'vehicle', 'slot'
    ).order_by('-created_at')[:10]

    # Floor stats
    floors = ParkingFloor.objects.filter(is_active=True)

    # Booking stats by status
    booking_stats = Booking.objects.values('status').annotate(count=Count('id'))

    # Messages
    unread_messages = ContactMessage.objects.filter(is_read=False).count()

    context = {
        'total_slots': total_slots,
        'available_slots': available_slots,
        'occupied_slots': occupied_slots,
        'total_users': total_users,
        'total_bookings': total_bookings,
        'active_bookings': active_bookings,
        'total_revenue': total_revenue,
        'recent_bookings': recent_bookings,
        'floors': floors,
        'booking_stats': booking_stats,
        'unread_messages': unread_messages,
        'occupancy_rate': round((occupied_slots / total_slots * 100) if total_slots > 0 else 0, 1),
    }
    return render(request, 'parking/admin_dashboard.html', context)


@login_required
def admin_manage_slots(request):
    """Admin: Manage parking slots"""
    if not request.user.is_staff:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    floors = ParkingFloor.objects.filter(is_active=True).prefetch_related('slots')
    slots = ParkingSlot.objects.select_related('floor').all()

    # Filter
    floor_filter = request.GET.get('floor', '')
    status_filter = request.GET.get('status', '')
    if floor_filter:
        slots = slots.filter(floor_id=floor_filter)
    if status_filter:
        slots = slots.filter(status=status_filter)

    context = {
        'floors': floors,
        'slots': slots,
        'floor_filter': floor_filter,
        'status_filter': status_filter,
    }
    return render(request, 'parking/admin_manage_slots.html', context)


@login_required
def admin_toggle_slot(request, slot_id):
    """Admin: Toggle slot status (maintenance/available)"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Access denied'}, status=403)

    slot = get_object_or_404(ParkingSlot, id=slot_id)
    if slot.status == 'maintenance':
        slot.status = 'available'
    elif slot.status == 'available':
        slot.status = 'maintenance'
    else:
        return JsonResponse({'error': 'Cannot toggle occupied/reserved slot'}, status=400)

    slot.save()
    messages.success(request, f'Slot {slot.slot_number} status changed to {slot.status}.')
    return redirect('admin_manage_slots')


@login_required
def admin_all_bookings(request):
    """Admin: View all bookings"""
    if not request.user.is_staff:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    bookings = Booking.objects.select_related(
        'user', 'vehicle', 'slot', 'payment'
    ).all()

    status_filter = request.GET.get('status', '')
    if status_filter:
        bookings = bookings.filter(status=status_filter)

    context = {
        'bookings': bookings,
        'status_filter': status_filter,
    }
    return render(request, 'parking/admin_all_bookings.html', context)


@login_required
def admin_messages(request):
    """Admin: View contact messages"""
    if not request.user.is_staff:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    msgs = ContactMessage.objects.all()
    return render(request, 'parking/admin_messages.html', {'contact_messages': msgs})


@login_required
def admin_mark_message_read(request, msg_id):
    """Admin: Mark message as read"""
    if not request.user.is_staff:
        return redirect('dashboard')

    msg = get_object_or_404(ContactMessage, id=msg_id)
    msg.is_read = True
    msg.save()
    return redirect('admin_messages')


# ========================
# API VIEWS (for AJAX)
# ========================

def api_slot_availability(request):
    """API: Get real-time slot availability"""
    floors = ParkingFloor.objects.filter(is_active=True)
    data = []
    for floor in floors:
        data.append({
            'floor': floor.name,
            'floor_number': floor.floor_number,
            'total': floor.total_slots,
            'available': floor.available_slots,
            'occupied': floor.occupied_slots,
        })
    return JsonResponse({'floors': data})


@login_required
def api_slot_info(request, slot_id):
    """API: Get slot details"""
    slot = get_object_or_404(ParkingSlot, id=slot_id)
    data = {
        'id': slot.id,
        'slot_number': slot.slot_number,
        'floor': slot.floor.name,
        'slot_type': slot.get_slot_type_display(),
        'status': slot.status,
        'hourly_rate': float(slot.hourly_rate),
    }
    return JsonResponse(data)
