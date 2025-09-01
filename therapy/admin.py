from django.contrib import admin
from .models import TherapistProfile, ParentProfile, Child, Assignment, Goal, Task
from users.models import Role, User
from users.utils import create_user_with_role
from django import forms
from neuvii_backend.admin_sites import neuvii_admin_site

class ChildForm(forms.ModelForm):
    class Meta:
        model = Child
        fields = ['name', 'age', 'gender', 'parent', 'assigned_therapist']
        
    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        # Store request and parent_obj for later use
        self.request = getattr(self, 'request', request)
        self.parent_obj = getattr(self, 'parent_obj', None)
        
        # Filter therapists based on clinic
        if self.request and hasattr(self.request.user, 'role') and self.request.user.role:
            if self.request.user.role.name.lower() == 'clinic admin':
                from clinic.models import Clinic
                try:
                    clinic = Clinic.objects.get(clinic_admin=self.request.user)
                    self.fields['assigned_therapist'].queryset = TherapistProfile.objects.filter(clinic=clinic)
                except Clinic.DoesNotExist:
                    self.fields['assigned_therapist'].queryset = TherapistProfile.objects.none()
            elif self.request.user.role.name.lower() == 'therapist':
                # Therapist can only assign themselves
                try:
                    therapist_profile = TherapistProfile.objects.get(email=self.request.user.email)
                    self.fields['assigned_therapist'].queryset = TherapistProfile.objects.filter(id=therapist_profile.id)
                except TherapistProfile.DoesNotExist:
                    self.fields['assigned_therapist'].queryset = TherapistProfile.objects.none()
        
        # Filter parents based on clinic for clinic admin
        if self.request and hasattr(self.request.user, 'role') and self.request.user.role:
            if self.request.user.role.name.lower() == 'clinic admin':
                from clinic.models import Clinic
                try:
                    clinic = Clinic.objects.get(clinic_admin=self.request.user)
                    self.fields['parent'].queryset = ParentProfile.objects.filter(clinic=clinic)
                except Clinic.DoesNotExist:
                    self.fields['parent'].queryset = ParentProfile.objects.none()
            elif self.request.user.role.name.lower() == 'parent':
                # Parent can only select themselves
                try:
                    parent_profile = ParentProfile.objects.get(parent_email=self.request.user.email)
                    self.fields['parent'].queryset = ParentProfile.objects.filter(id=parent_profile.id)
                except ParentProfile.DoesNotExist:
                    self.fields['parent'].queryset = ParentProfile.objects.none()

    def clean(self):
        cleaned_data = super().clean()
        
        # Ensure clinic is set for the child
        if not cleaned_data.get('clinic'):
            # Try to get clinic from parent first
            parent = cleaned_data.get('parent') or self.parent_obj
            if parent and parent.clinic:
                cleaned_data['clinic'] = parent.clinic
            # If no parent clinic, try to get from assigned therapist
            elif cleaned_data.get('assigned_therapist') and cleaned_data['assigned_therapist'].clinic:
                cleaned_data['clinic'] = cleaned_data['assigned_therapist'].clinic
            # If still no clinic, try to get from current user (clinic admin)
            elif self.request and hasattr(self.request.user, 'role') and self.request.user.role:
                if self.request.user.role.name.lower() == 'clinic admin':
                    from clinic.models import Clinic
                    try:
                        clinic = Clinic.objects.get(clinic_admin=self.request.user)
                        cleaned_data['clinic'] = clinic
                    except Clinic.DoesNotExist:
                        pass
        
        # If we still don't have a clinic, raise validation error
        if not cleaned_data.get('clinic'):
            raise forms.ValidationError('Could not determine clinic for this child. Please ensure the parent or therapist has a clinic assigned.')
        
        return cleaned_data


class TherapistProfileForm(forms.ModelForm):
    class Meta:
        model = TherapistProfile
        fields = '__all__'
        widgets = {
            'date_added': forms.DateInput(attrs={'type': 'date'}),
        }

class TherapistProfileAdmin(admin.ModelAdmin):
    form = TherapistProfileForm
    list_display = ['id', 'first_name', 'last_name', 'email', 'phone_number', 'is_active', 'date_added']
    search_fields = ['first_name', 'last_name', 'email', 'phone_number']
    list_filter = ['is_active', 'date_added']
    exclude = ['clinic']  # Hide clinic field from form
    readonly_fields = ['date_added']
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'email', 'phone')
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
            # For superusers, show the clinic field as a dropdown
            elif self.request.user.is_superuser:
                from clinic.models import Clinic
                self.fields['clinic'].queryset = Clinic.objects.all()
    
    def clean(self):
        cleaned_data = super().clean()
        # Ensure clinic is set
        if 'clinic' not in cleaned_data or not cleaned_data['clinic']:
            if self.request and hasattr(self.request.user, 'role') and self.request.user.role:
                if self.request.user.role.name.lower() == 'clinic admin':
                    from clinic.models import Clinic
                    try:
                        cleaned_data['clinic'] = Clinic.objects.get(clinic_admin=self.request.user)
                    except Clinic.DoesNotExist:
                        raise forms.ValidationError('No clinic is associated with your admin account.')
                else:
                    raise forms.ValidationError('A clinic must be selected.')
        return cleaned_data
       

class ChildInline(admin.TabularInline):
    model = Child
    form = ChildForm
    extra = 1
    fields = ('name', 'age', 'gender', 'assigned_therapist')
    autocomplete_fields = ['assigned_therapist']
    
    def get_formset(self, request, obj=None, **kwargs):
        FormSet = super().get_formset(request, obj, **kwargs)
        
        class ChildFormSetWithRequest(FormSet):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                for form in self.forms:
                    form.request = request
                    form.parent_obj = obj  # Pass the parent object
            
            def save_new(self, form, commit=True):
                """Override save_new to ensure clinic is set before saving"""
                obj = super().save_new(form, commit=False)
                
                # Auto-assign clinic admin's clinic to the child
                if hasattr(request.user, 'role') and request.user.role:
                    if request.user.role.name.lower() == 'clinic admin':
                        from clinic.models import Clinic
                        try:
                            clinic = Clinic.objects.get(clinic_admin=request.user)
                            obj.clinic = clinic
                        except Clinic.DoesNotExist:
                            from django.core.exceptions import ValidationError
                            raise ValidationError('No clinic is associated with your admin account.')
                    else:
                        from django.core.exceptions import ValidationError
                        raise ValidationError('Only clinic admins can add children.')
                else:
                    from django.core.exceptions import ValidationError
                    raise ValidationError('User role not found.')
                
                if commit:
                    obj.save()
                return obj
            
            def save_existing(self, form, instance, commit=True):
                """Override save_existing to ensure clinic is set before saving"""
                obj = super().save_existing(form, instance, commit=False)
                
                # Auto-assign clinic admin's clinic to the child if not set
                if not obj.clinic:
                    if hasattr(request.user, 'role') and request.user.role:
                        if request.user.role.name.lower() == 'clinic admin':
                            from clinic.models import Clinic
                            try:
                                clinic = Clinic.objects.get(clinic_admin=request.user)
                                obj.clinic = clinic
                            except Clinic.DoesNotExist:
                                from django.core.exceptions import ValidationError
                                raise ValidationError('No clinic is associated with your admin account.')
                
                if commit:
                    obj.save()
                return obj
        
        return ChildFormSetWithRequest

class ParentProfileAdmin(admin.ModelAdmin):
    form = ParentProfileForm
    list_display = ['id', 'first_name', 'last_name', 'phone_number', 'parent_email', 'clinic', 'date_added', 'is_active']
    search_fields = ['first_name', 'last_name', 'phone_number', 'parent_email', 'clinic__name']
    list_filter = ['clinic', 'is_active', 'date_added']
    inlines = [ChildInline]
    
    def get_form(self, request, obj=None, **kwargs):
        # Pass the request to the form
        kwargs['form'] = self.form
        form = super().get_form(request, obj, **kwargs)
        form.request = request
        return form
    
    def get_fieldsets(self, request, obj=None):
        fieldsets = [
            (None, {
                'fields': ('first_name', 'last_name', 'phone_number', 'parent_email', 'is_active')
            }),
        ]
        # Only show clinic field to superusers and clinic admins
        if request.user.is_superuser or (hasattr(request.user, 'role') and request.user.role.name.lower() == 'clinic admin'):
            fieldsets.append(('Clinic', {
                'fields': ('clinic',),
                'classes': ('collapse',)
            }))
        return fieldsets
        
    def get_readonly_fields(self, request, obj=None):
        # Make clinic read-only if user is a clinic admin
        if hasattr(request.user, 'role') and request.user.role and request.user.role.name.lower() == 'clinic admin':
            return ['clinic']
        return []
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        
        # Superuser sees all parents
        if request.user.is_superuser:
            return qs
            
        # Parent sees only their own profile
        if hasattr(request.user, 'role') and request.user.role:
            if request.user.role.name.lower() == 'parent':
                return qs.filter(parent_email=request.user.email)
            # Clinic admin sees only clients in their clinic
            elif request.user.role.name.lower() == 'clinic admin':
                from clinic.models import Clinic
                try:
                    clinic = Clinic.objects.get(clinic_admin=request.user)
                    return qs.filter(clinic=clinic)
                except Clinic.DoesNotExist:
                    pass
            # Therapists see parents of children they're assigned to
            elif request.user.role.name.lower() == 'therapist':
                try:
                    therapist_profile = TherapistProfile.objects.get(email=request.user.email)
                    # Show parents of children assigned to this therapist
                    from therapy.models import Child
                    therapist_children = Child.objects.filter(assigned_therapist=therapist_profile)
                    parent_emails = therapist_children.values_list('parent__parent_email', flat=True).distinct()
                    parent_emails = [email for email in parent_emails if email]
                    
                    return qs.filter(parent_email__in=parent_emails)
                except TherapistProfile.DoesNotExist:
                    pass
        
        return qs.none()
    list_filter = ['first_name', 'date_added', 'is_active']
    inlines = [ChildInline]
        
    def get_actions(self, request):
        actions = super().get_actions(request)
        actions['change_activation'] = (
            self.change_activation,
            'change_activation',
            'Mark selected parents as active/inactive'
        )
        return actions
        
    def change_activation(self, request, queryset):
        for parent in queryset:
            parent.is_active = not parent.is_active
            parent.save()
    change_activation.short_description = "Toggle activation status of selected parents"

    def save_model(self, request, obj, form, change):
        # The clinic should be set in form.clean()
        if not change and obj.first_name and obj.parent_email:
            try:
                parent_user = create_user_with_role(
                    email=obj.parent_email,
                    first_name=obj.first_name,
                    last_name=obj.last_name or "",
                    role_name='parent',
                    request=request
                )
            except Exception as e:
                # Log the error but don't fail the save
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f'Failed to create user for parent: {str(e)}')
        
        super().save_model(request, obj, form, change)

class ChildAdmin(admin.ModelAdmin):
    form = ChildForm
    list_display = ['id', 'name', 'age', 'gender', 'clinic', 'parent', 'assigned_therapist', 'created_at']
    search_fields = ['name', 'parent__first_name', 'parent__last_name', 'assigned_therapist__first_name', 'assigned_therapist__last_name']
    list_filter = ['clinic', 'gender', 'created_at']
    
    def get_form(self, request, obj=None, **kwargs):
        FormClass = super().get_form(request, obj, **kwargs)
        
        class FormWithRequest(FormClass):
            def __new__(cls, *args, **kwargs):
                kwargs['request'] = request
                return FormClass(*args, **kwargs)
        
        return FormWithRequest
    
    def save_model(self, request, obj, form, change):
        # Try to get clinic from parent first
        if obj.parent and obj.parent.clinic:
            obj.clinic = obj.parent.clinic
        # If no parent or parent has no clinic, try to get from therapist
        elif obj.assigned_therapist and obj.assigned_therapist.clinic:
            obj.clinic = obj.assigned_therapist.clinic
        # If still no clinic, try to get from current user's clinic (for clinic admins)
        elif hasattr(request.user, 'role') and request.user.role:
            if request.user.role.name.lower() == 'clinic admin':
                from clinic.models import Clinic
                try:
                    clinic = Clinic.objects.get(clinic_admin=request.user)
                    obj.clinic = clinic
                except Clinic.DoesNotExist:
                    pass
        
        # If we still don't have a clinic, raise validation error
        if not obj.clinic:
            from django.core.exceptions import ValidationError
            raise ValidationError('Could not determine clinic. Please ensure either parent or therapist has a clinic assigned.')
            
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        
        # Superuser sees all children
        if request.user.is_superuser:
            return qs
            
        # Filter based on user role
        if hasattr(request.user, 'role') and request.user.role:
            if request.user.role.name.lower() == 'clinic admin':
                # Get the clinic this admin manages
                from clinic.models import Clinic
                try:
                    clinic = Clinic.objects.get(clinic_admin=request.user)
                    return qs.filter(clinic=clinic)
                except Clinic.DoesNotExist:
                    pass
            elif request.user.role.name.lower() == 'therapist':
                # Show children assigned to this therapist
                try:
                    therapist_profile = TherapistProfile.objects.get(email=request.user.email)
                    return qs.filter(assigned_therapist=therapist_profile)
                except TherapistProfile.DoesNotExist:
                    pass
            elif request.user.role.name.lower() == 'parent':
                # Show children of this parent
                try:
                    parent_profile = ParentProfile.objects.get(parent_email=request.user.email)
                    return qs.filter(parent=parent_profile)
                except ParentProfile.DoesNotExist:
                    pass
        
        return qs.none()

# Register models with custom admin site
neuvii_admin_site.register(TherapistProfile, TherapistProfileAdmin)
neuvii_admin_site.register(ParentProfile, ParentProfileAdmin)
neuvii_admin_site.register(Child, ChildAdmin)

# Hidden for now - Tasks, Assignments, and Goals are not needed in current phase
# @admin.register(Assignment)
# class AssignmentAdmin(admin.ModelAdmin):
#     list_display = ['id', 'child', 'therapist', 'task', 'due_date', 'completed', 'assigned_date']
#     list_filter = ['therapist', 'child', 'completed', 'due_date']
#     search_fields = ['child__name', 'therapist__user__username', 'task__title']

# @admin.register(Goal)
# class GoalAdmin(admin.ModelAdmin):
#     list_display = ['id', 'child', 'title', 'is_long_term']
#     list_filter = ['is_long_term', 'child']
#     search_fields = ['title', 'child__name']

# @admin.register(Task)
# class TaskAdmin(admin.ModelAdmin):
#     list_display = ['id', 'goal', 'title', 'difficulty']
#     list_filter = ['difficulty', 'goal']
#     search_fields = ['title', 'goal__title']

