from django.contrib import admin
from .models import TherapistProfile, ClientProfile, Goal, Task, Assignment
from users.models import Role, User
from users.utils import create_user_with_role
from django import forms
from neuvii_backend.admin_sites import neuvii_admin_site

class ClientProfileForm(forms.ModelForm):
    class Meta:
        model = ClientProfile
        fields = [
            'child_first_name', 'child_last_name', 'parent_email',
            'child_date_of_birth', 'fscd_id', 'assigned_therapist'
        ]
        widgets = {
            'child_date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'child_first_name': forms.TextInput(attrs={'placeholder': 'Enter first name'}),
            'child_last_name': forms.TextInput(attrs={'placeholder': 'Enter last name'}),
            'parent_email': forms.EmailInput(attrs={'placeholder': 'Enter your email'}),
            'fscd_id': forms.TextInput(attrs={'placeholder': 'FSCD76439'}),
        }
        
    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        self.request = request
        
        # Filter therapists based on clinic
        if self.request and hasattr(self.request.user, 'role') and self.request.user.role:
            if self.request.user.role.name.lower() == 'clinic admin':
                from clinic.models import Clinic
                try:
                    clinic = Clinic.objects.get(clinic_admin=self.request.user)
                    self.fields['assigned_therapist'].queryset = TherapistProfile.objects.filter(clinic=clinic)
                    self.fields['assigned_therapist'].empty_label = "Select Therapist"
                except Clinic.DoesNotExist:
                    self.fields['assigned_therapist'].queryset = TherapistProfile.objects.none()
            elif self.request.user.role.name.lower() == 'therapist':
                try:
                    therapist_profile = TherapistProfile.objects.get(email=self.request.user.email)
                    self.fields['assigned_therapist'].queryset = TherapistProfile.objects.filter(id=therapist_profile.id)
                    self.fields['assigned_therapist'].initial = therapist_profile
                except TherapistProfile.DoesNotExist:
                    self.fields['assigned_therapist'].queryset = TherapistProfile.objects.none()

    def clean(self):
        cleaned_data = super().clean()
        
        # Auto-assign clinic based on user role
        if self.request and hasattr(self.request.user, 'role') and self.request.user.role:
            if self.request.user.role.name.lower() == 'clinic admin':
                from clinic.models import Clinic
                try:
                    clinic = Clinic.objects.get(clinic_admin=self.request.user)
                    # Store clinic for save_model method
                    self._clinic = clinic
                except Clinic.DoesNotExist:
                    raise forms.ValidationError('No clinic is associated with your admin account.')
            elif self.request.user.role.name.lower() == 'therapist':
                try:
                    therapist_profile = TherapistProfile.objects.get(email=self.request.user.email)
                    if therapist_profile.clinic:
                        self._clinic = therapist_profile.clinic
                    else:
                        raise forms.ValidationError('Your therapist profile is not associated with any clinic.')
                except TherapistProfile.DoesNotExist:
                    raise forms.ValidationError('Therapist profile not found.')
        
        return cleaned_data


class ClientProfileAdmin(admin.ModelAdmin):
    form = ClientProfileForm
    list_display = [
        'id', 'child_full_name', 'child_age', 'parent_email',
        'assigned_therapist', 'clinic', 'fscd_id', 'is_active', 'date_added'
    ]
    search_fields = [
        'child_first_name', 'child_last_name', 'parent_email', 'fscd_id'
    ]
    list_filter = ['clinic', 'assigned_therapist', 'is_active', 'date_added']
    
    fieldsets = (
        ('Child Information', {
            'fields': (
                ('child_first_name', 'child_last_name'),
                'child_date_of_birth',
            )
        }),
        ('Parent Information', {
            'fields': (
                'parent_email',
            )
        }),
        ('Administrative', {
            'fields': (
                'fscd_id',
                'assigned_therapist',
            )
        }),
        ('Status', {
            'fields': ('is_active',),
        }),
    )
    
    def get_form(self, request, obj=None, **kwargs):
        FormClass = super().get_form(request, obj, **kwargs)
        
        class FormWithRequest(FormClass):
            def __new__(cls, *args, **kwargs):
                kwargs['request'] = request
                return FormClass(*args, **kwargs)
        
        return FormWithRequest
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        
        # Superuser sees all clients
        if request.user.is_superuser:
            return qs
            
        # Filter based on user role
        if hasattr(request.user, 'role') and request.user.role:
            if request.user.role.name.lower() == 'clinic admin':
                from clinic.models import Clinic
                try:
                    clinic = Clinic.objects.get(clinic_admin=request.user)
                    return qs.filter(clinic=clinic)
                except Clinic.DoesNotExist:
                    pass
            elif request.user.role.name.lower() == 'therapist':
                try:
                    therapist_profile = TherapistProfile.objects.get(email=request.user.email)
                    return qs.filter(assigned_therapist=therapist_profile)
                except TherapistProfile.DoesNotExist:
                    pass
            elif request.user.role.name.lower() == 'parent':
                return qs.filter(parent_email=request.user.email)
        
        return qs.none()

    def save_model(self, request, obj, form, change):
        # Auto-assign clinic from form
        if hasattr(form, '_clinic'):
            obj.clinic = form._clinic
        
        # Save the client profile
        super().save_model(request, obj, form, change)
        
        # Auto-create parent user if email is provided and it's a new client
        if obj.parent_email and not change:
            # Extract parent name from child's name for user creation
            parent_user = create_user_with_role(
                email=obj.parent_email,
                first_name=obj.child_first_name,  # Use child's first name as placeholder
                last_name=obj.child_last_name,   # Use child's last name as placeholder
                role_name='parent',
                request=request
            )


class TherapistProfileForm(forms.ModelForm):
    class Meta:
        model = TherapistProfile
        fields = '__all__'
        widgets = {
            'date_added': forms.DateInput(attrs={'type': 'date'}),
        }

class TherapistProfileAdmin(admin.ModelAdmin):
    form = TherapistProfileForm
    list_display = ['id', 'first_name', 'last_name', 'email', 'phone_number', 'clinic', 'is_active', 'date_added']
    search_fields = ['first_name', 'last_name', 'email', 'phone_number']
    list_filter = ['clinic', 'is_active', 'date_added']
    exclude = ['clinic']
    readonly_fields = ['date_added']
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'email', 'phone_number')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('date_added',),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        
        # Superuser sees all therapists
        if request.user.is_superuser:
            return qs.order_by('last_name', 'first_name')
            
        # Therapist sees only their own profile
        if hasattr(request.user, 'role') and request.user.role:
            if request.user.role.name.lower() == 'therapist':
                return qs.filter(email=request.user.email)
            # Clinic admin sees only therapists in their clinic
            elif request.user.role.name.lower() == 'clinic admin':
                from clinic.models import Clinic
                try:
                    clinic = Clinic.objects.get(clinic_admin=request.user)
                    return qs.filter(clinic=clinic).order_by('last_name', 'first_name')
                except Clinic.DoesNotExist:
                    pass
        
        return qs.none()

    def save_model(self, request, obj, form, change):
        # Auto-assign clinic if clinic admin is creating the therapist
        if not change and hasattr(request.user, 'role') and request.user.role:
            if request.user.role.name.lower() == 'clinic admin':
                from clinic.models import Clinic
                try:
                    clinic = Clinic.objects.get(clinic_admin=request.user)
                    obj.clinic = clinic
                except Clinic.DoesNotExist:
                    pass
        
        # Save the therapist profile
        super().save_model(request, obj, form, change)
        
        # Auto-create therapist user if email and name are provided
        if obj.first_name and obj.email and not change:  # Only for new therapists
            therapist_user = create_user_with_role(
                email=obj.email,
                first_name=obj.first_name,
                last_name=obj.last_name or "",
                role_name='therapist',
                request=request
            )


# Register only the new unified models with custom admin site
neuvii_admin_site.register(ClientProfile, ClientProfileAdmin)
neuvii_admin_site.register(TherapistProfile, TherapistProfileAdmin)

# Note: Child and ParentProfile models are no longer registered with the admin site
# They exist only for data migration purposes and are hidden from the interface