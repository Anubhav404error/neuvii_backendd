from django.db import models
from users.models import User

class Clinic(models.Model):
    name = models.CharField(max_length=255)
    address_line_1 = models.CharField(max_length=255, blank=True, null=True)
    address_line_2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    contact_person_name = models.CharField(max_length=255, blank=True, null=True)
    role = models.CharField(max_length=100, blank=True, null=True)  # e.g. Director
    email = models.EmailField(blank=True, null=True)
    clinic_admin = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, related_name='clinic_admin')
    agreement_signed = models.BooleanField(default=False)
    consent_template = models.FileField(upload_to='clinic_docs/', blank=True, null=True)
    license_status = models.CharField(max_length=50, choices=[('Active', 'Active'), ('Inactive', 'Inactive')], blank=True, null=True)
    internal_notes = models.TextField(blank=True, null=True)
    logo = models.ImageField(upload_to='clinic_logos/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
