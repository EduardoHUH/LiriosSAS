from rest_framework.throttling import AnonRateThrottle


class BookingCreateThrottle(AnonRateThrottle):
    scope = "booking_create"


class AppointmentActionThrottle(AnonRateThrottle):
    scope = "appointment_action"
