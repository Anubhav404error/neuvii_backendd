from django.contrib import admin
from .models import TherapistProfile, ParentProfile, Child, ClientProfile, Assignment, Goal, Task
from users.models import Role, User
from users.utils import create_user_with_role
from django import forms
from neuvii_backend.admin_sites import neuvii_admin_site

class ClientProfileForm(forms.ModelForm):
    class Meta:
        model = ClientProfile
        fields = '__all__'
        widgets = {
            'child_date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'medical_notes': forms.Textarea(attrs={'rows': 3}),
            'therapy_goals': forms.Textarea(attrs={'rows': 3}),
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
                    self.fields['clinic'].initial = clinic
                    self.fields['clinic'].widget = forms.HiddenInput()
                except Clinic.DoesNotExist:
                    self.fields['assigned_therapist'].queryset = TherapistProfile.objects.none()
            elif self.request.user.role.name.lower() == 'therapist':
                # Therapist can only assign themselves
                try:
                    therapist_profile = TherapistProfile.objects.get(email=self.request.user.email)
                    self.fields['assigned_therapist'].queryset = TherapistProfile.objects.filter(id=therapist_profile.id)
                    self.fields['assigned_therapist'].initial = therapist_profile
                    if therapist_profile.clinic:
                        self.fields['clinic'].initial = therapist_profile.clinic
                        self.fields['clinic'].widget = forms.HiddenInput()
                except TherapistProfile.DoesNotExist:
                    self.fields['assigned_therapist'].queryset = TherapistProfile.objects.none()

    def clean(self):
        cleaned_data = super().clean()
        
        # Auto-assign clinic based on user role
        if not cleaned_data.get('clinic'):
            if self.request and hasattr(self.request.user, 'role') and self.request.user.role:
                if self.request.user.role.name.lower() == 'clinic admin':
                    from clinic.models import Clinic
                    try:
                        clinic = Clinic.objects.get(clinic_admin=self.request.user)
                        cleaned_data['clinic'] = clinic
                    except Clinic.DoesNotExist:
                        raise forms.ValidationError('No clinic is associated with your admin account.')
                elif self.request.user.role.name.lower() == 'therapist':
                    try:
                        therapist_profile = TherapistProfile.objects.get(email=self.request.user.email)
                        if therapist_profile.clinic:
                            cleaned_data['clinic'] = therapist_profile.clinic
                        else:
                            raise forms.ValidationError('Your therapist profile is not associated with any clinic.')
                    except TherapistProfile.DoesNotExist:
                        raise forms.ValidationError('Therapist profile not found.')
        
        return cleaned_data


class ClientProfileAdmin(admin.ModelAdmin):
    form = ClientProfileForm
    list_display = [
        'id', 'parent_full_name', 'child_full_name', 'child_age', 
        'assigned_therapist', 'clinic', 'fscd_id', 'is_active', 'date_added'
    ]
    search_fields = [
        'parent_first_name', 'parent_last_name', 'parent_email',
        'child_first_name', 'child_last_name', 'fscd_id'
    ]
    list_filter = ['clinic', 'assigned_therapist', 'child_gender', 'is_active', 'date_added']
    exclude = ['clinic'] if not hasattr(admin, 'site') else []
    
    fieldsets = (
        ('Parent Information', {
            'fields': (
                ('parent_first_name', 'parent_last_name'),
                ('parent_email', 'parent_phone'),
            )
        }),
        ('Child Information', {
            'fields': (
                ('child_first_name', 'child_last_name'),
                ('child_date_of_birth', 'child_gender'),
            )
        }),
        ('Administrative', {
            'fields': (
                ('fscd_id', 'assigned_therapist'),
            )
        }),
        ('Emergency Contact', {
            'fields': (
                ('emergency_contact_name', 'emergency_contact_phone'),
            ),
            'classes': ('collapse',)
        }),
        ('Therapy Information', {
            'fields': (
                'medical_notes',
                'therapy_goals',
            ),
            'classes': ('collapse',)
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
        # Auto-assign clinic if not set
        if not obj.clinic:
            if hasattr(request.user, 'role') and request.user.role:
                if request.user.role.name.lower() == 'clinic admin':
                    from clinic.models import Clinic
                    try:
                        clinic = Clinic.objects.get(clinic_admin=request.user)
                        obj.clinic = clinic
                    except Clinic.DoesNotExist:
                        pass
                elif request.user.role.name.lower() == 'therapist':
                    try:
                        therapist_profile = TherapistProfile.objects.get(email=request.user.email)
                        if therapist_profile.clinic:
                            obj.clinic = therapist_profile.clinic
                    except TherapistProfile.DoesNotExist:
                        pass
        
        # Save the client profile
        super().save_model(request, obj, form, change)
        
        # Auto-create parent user if email and name are provided
        if obj.parent_first_name and obj.parent_email and not change:  # Only for new clients
            parent_user = create_user_with_role(
                email=obj.parent_email,
                first_name=obj.parent_first_name,
                last_name=obj.parent_last_name or "",
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
    exclude = ['clinic']  # Hide clinic field from form
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


# Legacy admin classes (hidden from main interface but kept for data migration)
class ParentProfileForm(forms.ModelForm):
    class Meta:
        model = ParentProfile
        fields = '__all__'
        
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        # Handle clinic field based on user role
        if self.request and hasattr(self.request.user, 'role') and self.request.user.role:
            if self.request.user.role.name.lower() == 'clinic admin':
                from clinic.models import Clinic
                try:
                    clinic = Clinic.objects.get(clinic_admin=self.request.user)
                    self.fields['clinic'].initial = clinic
                    self.fields['clinic'].widget = forms.HiddenInput()
                except Clinic.DoesNotExist:
                    pass

class ParentProfileAdmin(admin.ModelAdmin):
    form = ParentProfileForm
    list_display = ['id', 'first_name', 'last_name', 'phone_number', 'parent_email', 'clinic', 'date_added', 'is_active']
    search_fields = ['first_name', 'last_name', 'phone_number', 'parent_email', 'clinic__name']
    list_filter = ['clinic', 'is_active', 'date_added']

class ChildForm(forms.ModelForm):
    class Meta:
        model = Child
        fields = ['name', 'age', 'gender', 'parent', 'assigned_therapist']

class ChildAdmin(admin.ModelAdmin):
    form = ChildForm
    list_display = ['id', 'name', 'age', 'gender', 'clinic', 'parent', 'assigned_therapist', 'created_at']
    search_fields = ['name', 'parent__first_name', 'parent__last_name']
    list_filter = ['clinic', 'gender', 'created_at']


# Register new models with custom admin site
neuvii_admin_site.register(ClientProfile, ClientProfileAdmin)
neuvii_admin_site.register(TherapistProfile, TherapistProfileAdmin)

# Keep legacy models registered but hidden (for data migration purposes)
# These won't show in the main interface due to admin_sites.py filtering
admin.site.register(ParentProfile, ParentProfileAdmin)
admin.site.register(Child, ChildAdmin)