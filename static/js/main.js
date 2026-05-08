/* ===========================
   Smart Parking System - JavaScript
   =========================== */

// Mobile navbar toggle
document.addEventListener('DOMContentLoaded', function() {
    const toggle = document.querySelector('.navbar-toggle');
    const nav = document.querySelector('.navbar-nav');

    if (toggle && nav) {
        toggle.addEventListener('click', function() {
            nav.classList.toggle('active');
        });
    }

    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-10px)';
            setTimeout(function() {
                alert.remove();
            }, 300);
        }, 5000);
    });

    // Alert close buttons
    document.querySelectorAll('.alert-close').forEach(function(btn) {
        btn.addEventListener('click', function() {
            const alert = this.closest('.alert');
            alert.style.opacity = '0';
            setTimeout(function() { alert.remove(); }, 300);
        });
    });

    // Floor tabs for parking map
    const floorTabs = document.querySelectorAll('.floor-tab');
    const floorContents = document.querySelectorAll('.floor-content');

    floorTabs.forEach(function(tab) {
        tab.addEventListener('click', function() {
            const floor = this.dataset.floor;

            // Update active tab
            floorTabs.forEach(t => t.classList.remove('active'));
            this.classList.add('active');

            // Show/hide floor contents
            floorContents.forEach(function(content) {
                if (floor === 'all' || content.dataset.floor === floor) {
                    content.style.display = 'block';
                } else {
                    content.style.display = 'none';
                }
            });
        });
    });

    // Slot hover effect
    const slots = document.querySelectorAll('.parking-slot');
    slots.forEach(function(slot) {
        slot.addEventListener('mouseenter', function() {
            if (this.classList.contains('available')) {
                this.style.transform = 'scale(1.1)';
            }
        });
        slot.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1)';
        });
    });

    // Calculate estimated cost in booking form
    const hoursInput = document.querySelector('#id_expected_hours, input[name="expected_hours"]');
    const slotSelect = document.querySelector('#id_slot, select[name="slot"]');
    const costDisplay = document.querySelector('#estimated-cost');

    function updateCost() {
        if (hoursInput && costDisplay) {
            const hours = parseInt(hoursInput.value) || 1;
            const rateElement = document.querySelector('#slot-rate');
            const rate = rateElement ? parseFloat(rateElement.dataset.rate) : 50;
            const total = hours * rate;
            costDisplay.textContent = 'Rs. ' + total.toFixed(2);
        }
    }

    if (hoursInput) {
        hoursInput.addEventListener('input', updateCost);
    }
    if (slotSelect) {
        slotSelect.addEventListener('change', updateCost);
    }

    // Animate numbers on scroll
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(function(entry) {
            if (entry.isIntersecting) {
                const el = entry.target;
                const target = parseInt(el.dataset.target);
                if (target && !el.dataset.animated) {
                    el.dataset.animated = 'true';
                    animateNumber(el, target);
                }
            }
        });
    }, { threshold: 0.5 });

    document.querySelectorAll('[data-target]').forEach(function(el) {
        observer.observe(el);
    });

    // Real-time clock
    const clockEl = document.querySelector('#real-time-clock');
    if (clockEl) {
        setInterval(function() {
            const now = new Date();
            clockEl.textContent = now.toLocaleTimeString();
        }, 1000);
    }
});

// Animate number counting
function animateNumber(element, target) {
    let current = 0;
    const increment = target / 50;
    const timer = setInterval(function() {
        current += increment;
        if (current >= target) {
            current = target;
            clearInterval(timer);
        }
        element.textContent = Math.floor(current);
    }, 30);
}

// Refresh slot availability (called on parking map page)
function refreshAvailability() {
    fetch('/api/availability/')
        .then(response => response.json())
        .then(data => {
            console.log('Availability updated:', data);
            // Update UI if needed
        })
        .catch(error => console.error('Error:', error));
}

// Confirm actions
function confirmAction(message) {
    return confirm(message || 'Are you sure you want to proceed?');
}
