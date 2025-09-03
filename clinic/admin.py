from django.contrib import admin
from .models import Clinic
from neuvii_backend.admin_sites import neuvii_admin_site
from django import forms
from django.contrib import admin
from django.core.validators import RegexValidator
from .models import Clinic
from users.models import Role, User
from users.utils import create_user_with_role, parse_contact_person_name

# Custom ModelForm for Clinic
class ClinicForm(forms.ModelForm):
    class Meta:
        model = Clinic
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'clinic_admin' in self.fields:
            try:
                clinic_admin_role = Role.objects.get(name__iexact='clinic admin')
                self.fields['clinic_admin'].queryset = User.objects.filter(role=clinic_admin_role)
            except Role.DoesNotExist:
                self.fields['clinic_admin'].queryset = User.objects.none()

class ClinicAdmin(admin.ModelAdmin):
    form = ClinicForm
    list_display = ['id', 'name', 'clinic_admin', 'is_active', 'created_at']
    list_filter = ['name', 'is_active', 'created_at']
    search_fields = ['name']
    ordering = ['id']
    
    def get_queryset(self, request):
        """Filter clinics based on user role"""
        qs = super().get_queryset(request)
        
        # Superuser sees all clinics
        if request.user.is_superuser:
            return qs
            
        # Clinic admin sees only their own clinic
        if hasattr(request.user, 'role') and request.user.role:
            if request.user.role.name.lower() == 'clinic admin':
                return qs.filter(clinic_admin=request.user)
        
        # Default: no clinics visible
        return qs.none()
    
    def has_add_permission(self, request):
        """Only superusers can add new clinics"""
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete clinics"""
        return request.user.is_superuser

    fieldsets = (
        ('Basic Clinic Information', {
            'fields': (
                ('name' ),
                ('address_line_1', 'address_line_2' ),
                ('city', 'country'),
            ),
        }),
        ('Primary Contact Information', {
            'fields': (
                ('contact_person_name', 'role', 'email'),
            ),
        }),
        ('Compliance & Agreements', {
            'fields': (
                ('agreement_signed', 'consent_template', 'license_status'),
            ),
        }),
        ('White-Label Settings', {
            'fields': (
                'logo',
            ),
        }),
        ('Internal Notes', {
            'fields': ('internal_notes',),
            'description': 'Visible to Neuvii Admin Only',
        }),
    )

    def save_model(self, request, obj, form, change):
        # Save the clinic first
        super().save_model(request, obj, form, change)
        
        # Auto-create clinic admin user if contact person details are provided
        if obj.contact_person_name and obj.email and not obj.clinic_admin:
            first_name, last_name = parse_contact_person_name(obj.contact_person_name)
            
            if first_name:  # Only create if we have at least a first name
                clinic_admin_user = create_user_with_role(
                    email=obj.email,
                    first_name=first_name,
                    last_name=last_name,
                    role_name='clinic admin',
                    request=request
                )
                
                if clinic_admin_user:
                    obj.clinic_admin = clinic_admin_user
                    obj.save(update_fields=['clinic_admin'])

# Register with custom admin site
neuvii_admin_site.register(Clinic, ClinicAdmin)


