"""
Seed script to populate the database with sample data.
Run: python manage.py shell < seed_data.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_parking.settings')
django.setup()

from django.contrib.auth.models import User
from parking.models import UserProfile, ParkingFloor, ParkingSlot, Vehicle, Booking, Payment
from django.utils import timezone

print("=" * 50)
print("  Smart Parking System - Seeding Database")
print("=" * 50)

# ==============================
# Create Superuser (Admin)
# ==============================
if not User.objects.filter(username='admin').exists():
    admin_user = User.objects.create_superuser(
        username='admin',
        email='admin@smartpark.com',
        password='admin123',
        first_name='Admin',
        last_name='User'
    )
    UserProfile.objects.create(user=admin_user, phone='+92 300 0000000', address='Admin Office')
    print("[+] Admin user created (username: admin, password: admin123)")
else:
    admin_user = User.objects.get(username='admin')
    print("[*] Admin user already exists")

# ==============================
# Create Test Users
# ==============================
test_users = [
    {'username': 'ahmed', 'first_name': 'Ahmed', 'last_name': 'Khan', 'email': 'ahmed@example.com', 'phone': '+92 321 1111111'},
    {'username': 'sara', 'first_name': 'Sara', 'last_name': 'Ali', 'email': 'sara@example.com', 'phone': '+92 322 2222222'},
    {'username': 'ali', 'first_name': 'Ali', 'last_name': 'Hassan', 'email': 'ali@example.com', 'phone': '+92 323 3333333'},
]

created_users = []
for u_data in test_users:
    user, created = User.objects.get_or_create(
        username=u_data['username'],
        defaults={
            'first_name': u_data['first_name'],
            'last_name': u_data['last_name'],
            'email': u_data['email'],
        }
    )
    if created:
        user.set_password('test1234')
        user.save()
        UserProfile.objects.create(user=user, phone=u_data['phone'])
        print(f"[+] User created: {u_data['username']} (password: test1234)")
    else:
        print(f"[*] User already exists: {u_data['username']}")
    created_users.append(user)

# ==============================
# Create Parking Floors
# ==============================
floors_data = [
    {'name': 'Ground Floor', 'floor_number': 0},
    {'name': 'Floor 1', 'floor_number': 1},
    {'name': 'Floor 2', 'floor_number': 2},
    {'name': 'Floor 3 (Roof)', 'floor_number': 3},
]

created_floors = []
for f_data in floors_data:
    floor, created = ParkingFloor.objects.get_or_create(
        floor_number=f_data['floor_number'],
        defaults={'name': f_data['name']}
    )
    created_floors.append(floor)
    if created:
        print(f"[+] Floor created: {f_data['name']}")
    else:
        print(f"[*] Floor already exists: {f_data['name']}")

# ==============================
# Create Parking Slots
# ==============================
slot_configs = [
    # Ground Floor - 12 slots
    {'floor': 0, 'prefix': 'G', 'count': 12, 'types': ['regular', 'regular', 'regular', 'compact', 'compact', 'large', 'regular', 'regular', 'handicapped', 'ev', 'regular', 'regular']},
    # Floor 1 - 15 slots
    {'floor': 1, 'prefix': '1', 'count': 15, 'types': ['regular'] * 10 + ['compact'] * 3 + ['large', 'ev']},
    # Floor 2 - 15 slots
    {'floor': 2, 'prefix': '2', 'count': 15, 'types': ['regular'] * 8 + ['compact'] * 4 + ['large', 'handicapped', 'ev']},
    # Floor 3 - 10 slots
    {'floor': 3, 'prefix': '3', 'count': 10, 'types': ['regular'] * 5 + ['compact'] * 3 + ['large', 'ev']},
]

rates = {'compact': 30, 'regular': 50, 'large': 80, 'handicapped': 40, 'ev': 60}

total_slots_created = 0
for config in slot_configs:
    floor = ParkingFloor.objects.get(floor_number=config['floor'])
    for i in range(config['count']):
        slot_number = f"{config['prefix']}-{str(i+1).zfill(2)}"
        slot_type = config['types'][i] if i < len(config['types']) else 'regular'
        slot, created = ParkingSlot.objects.get_or_create(
            slot_number=slot_number,
            defaults={
                'floor': floor,
                'slot_type': slot_type,
                'status': 'available',
                'hourly_rate': rates.get(slot_type, 50),
            }
        )
        if created:
            total_slots_created += 1

print(f"[+] {total_slots_created} parking slots created")

# ==============================
# Create Sample Vehicles
# ==============================
vehicles_data = [
    {'user': created_users[0], 'plate': 'LEA-1234', 'type': 'car', 'make': 'Toyota', 'model': 'Corolla', 'color': 'White'},
    {'user': created_users[0], 'plate': 'LHR-5678', 'type': 'suv', 'make': 'Honda', 'model': 'HR-V', 'color': 'Black'},
    {'user': created_users[1], 'plate': 'ISB-9012', 'type': 'car', 'make': 'Suzuki', 'model': 'Swift', 'color': 'Red'},
    {'user': created_users[2], 'plate': 'KHI-3456', 'type': 'motorcycle', 'make': 'Honda', 'model': 'CB150', 'color': 'Blue'},
    {'user': created_users[2], 'plate': 'KHI-7890', 'type': 'car', 'make': 'Toyota', 'model': 'Yaris', 'color': 'Silver'},
]

created_vehicles = []
for v_data in vehicles_data:
    vehicle, created = Vehicle.objects.get_or_create(
        license_plate=v_data['plate'],
        defaults={
            'user': v_data['user'],
            'vehicle_type': v_data['type'],
            'make': v_data['make'],
            'model': v_data['model'],
            'color': v_data['color'],
        }
    )
    created_vehicles.append(vehicle)
    if created:
        print(f"[+] Vehicle created: {v_data['plate']}")

# ==============================
# Create Sample Bookings
# ==============================
now = timezone.now()
bookings_data = [
    # Active booking
    {
        'user': created_users[0],
        'vehicle': created_vehicles[0],
        'slot_number': 'G-01',
        'check_in': now - timezone.timedelta(hours=2),
        'expected_hours': 4,
        'status': 'active',
    },
    # Completed booking
    {
        'user': created_users[1],
        'vehicle': created_vehicles[2],
        'slot_number': '1-03',
        'check_in': now - timezone.timedelta(hours=5),
        'check_out': now - timezone.timedelta(hours=2),
        'expected_hours': 3,
        'status': 'completed',
    },
    # Another active booking
    {
        'user': created_users[2],
        'vehicle': created_vehicles[4],
        'slot_number': '2-05',
        'check_in': now - timezone.timedelta(hours=1),
        'expected_hours': 2,
        'status': 'active',
    },
]

for b_data in bookings_data:
    slot = ParkingSlot.objects.get(slot_number=b_data['slot_number'])
    
    # Only create if no active booking exists for this slot
    existing = Booking.objects.filter(slot=slot, status='active').exists()
    if not existing or b_data['status'] != 'active':
        booking = Booking.objects.create(
            user=b_data['user'],
            vehicle=b_data['vehicle'],
            slot=slot,
            check_in=b_data['check_in'],
            check_out=b_data.get('check_out'),
            expected_hours=b_data['expected_hours'],
            status=b_data['status'],
        )
        
        # Update slot status for active bookings
        if b_data['status'] == 'active':
            slot.status = 'occupied'
            slot.save()
        
        # Create payment
        amount = float(slot.hourly_rate) * b_data['expected_hours']
        Payment.objects.create(
            booking=booking,
            amount=amount,
            status='completed' if b_data['status'] == 'completed' else 'pending',
            payment_method='cash' if b_data['status'] == 'completed' else 'cash',
            paid_at=b_data.get('check_out') if b_data['status'] == 'completed' else None,
        )
        print(f"[+] Booking created: {booking.booking_id}")

# Set a couple of slots to maintenance
maintenance_slots = ParkingSlot.objects.filter(slot_number__in=['G-12', '3-10', '1-15'])
for slot in maintenance_slots:
    if slot.status == 'available':
        slot.status = 'maintenance'
        slot.save()
        print(f"[+] Slot {slot.slot_number} set to maintenance")

print("\n" + "=" * 50)
print("  Seeding Complete!")
print("=" * 50)
print("\n  Login Credentials:")
print("  -------------------")
print("  Admin:  admin / admin123")
print("  User 1: ahmed / test1234")
print("  User 2: sara  / test1234")
print("  User 3: ali   / test1234")
print("=" * 50)
