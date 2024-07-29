# database.py
from datetime import datetime
from django.utils import timezone
from property.models import Customer, Service, Staff, Salon, Appointment



def get_customer_by_telegram_id(telegram_id):
    try:
        return Customer.objects.get(telegram_id=telegram_id)
    except Customer.DoesNotExist:
        return None


def get_upcoming_appointments(customer):
    return Appointment.objects.filter(customer=customer, date_time__gte=timezone.now())


def get_available_salons():
    return Salon.objects.all()


def get_available_services():
    return Service.objects.all()


def get_available_staff(salon=None, service=None):
    staff_qs = Staff.objects.all()
    if salon:
        staff_qs = staff_qs.filter(salon=salon)
    if service:
        staff_qs = staff_qs.filter(services=service)
    return staff_qs


def create_appointment(customer, service, staff, salon, date_time):
    appointment = Appointment(customer=customer, salon=salon, staff=staff, date_time=date_time)
    appointment.save()
    appointment.services.add(service)
    return appointment


def delete_appointment(appointment_id):
    try:
        appointment = Appointment.objects.get(id=appointment_id)
        appointment.delete()
    except Appointment.DoesNotExist:
        pass
