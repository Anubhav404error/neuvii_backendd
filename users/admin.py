from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib import messages
from django.core.mail import send_mail
from django.contrib import admin
from .models import User, Role
from django import forms
from neuvii_backend.admin_sites import neuvii_admin_site
from .forms import CustomUserCreationForm, CustomUserChangeForm

admin.site.register(Role)


@admin.register(User, site=neuvii_admin_site)
class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User

    list_display = ['id', 'email', 'get_full_name', 'role', 'is_active', 'password_reset_required', 'created_at']
    list_filter = ['role', 'is_active', 'is_staff', 'is_superuser', 'password_reset_required', 'created_at']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['id']

    fieldsets = (
        (None, {'fields': ('email',)}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'role')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'role', 'is_active', 'is_staff', 'is_superuser'),
        }),
    )

    def get_queryset(self, request):
        """Filter users based on role"""
        qs = super().get_queryset(request)
        
        # Neuvii admin (superuser) sees all users
        if request.user.is_superuser:
            return qs
            
        # Clinic admin sees only users related to their clinic
        if hasattr(request.user, 'role') and request.user.role:
            if request.user.role.name.lower() == 'clinic admin':
                # Get the clinic this admin manages
                from clinic.models import Clinic
                try:
                    clinic = Clinic.objects.get(clinic_admin=request.user)
                    # Show therapists and parents directly linked to this clinic
                    from therapy.models import TherapistProfile, ParentProfile
                    therapist_emails = TherapistProfile.objects.filter(clinic=clinic).values_list('email', flat=True)
                    parent_emails = ParentProfile.objects.filter(clinic=clinic).values_list('parent_email', flat=True)
                    
                    # Filter users by role and email
                    clinic_user_emails = list(therapist_emails) + list(parent_emails)
                    clinic_user_emails = [email for email in clinic_user_emails if email]  # Remove None values
                    
                    return qs.filter(email__in=clinic_user_emails)
                except Clinic.DoesNotExist:
                    pass
        
        # Default: no users visible
        return qs.none()

    def get_form(self, request, obj=None, **kwargs):
        """Customize form based on user role"""
        form = super().get_form(request, obj, **kwargs)
        
        # Clinic admin can only create therapists and parents
        if hasattr(request.user, 'role') and request.user.role:
            if request.user.role.name.lower() == 'clinic admin':
                if 'role' in form.base_fields:
                    form.base_fields['role'].queryset = Role.objects.filter(
                        name__in=['Therapist', 'Parent']
                    )
        
        return form

    def save_model(self, request, obj, form, change):
        if not change:  # Only for new users
            # Generate temporary password
            temp_password = obj.generate_temp_password()
            obj.password_reset_required = True

            # Save the user first
            super().save_model(request, obj, form, change)

            # Send email with temporary password
            self.send_welcome_email(obj, temp_password)

            messages.success(
                request,
                f'User {obj.email} created successfully. Welcome email sent with temporary password.'
            )
        else:
            super().save_model(request, obj, form, change)

    def send_welcome_email(self, user, temp_password):
        """Send welcome email with temporary password"""
        subject = 'Welcome to Neuvii - Your Account Details'

        # Create password reset link
        reset_link = f"http://127.0.0.1:8000/auth/reset-password/?email={user.email}&temp_password={temp_password}"

        message = f"""
Welcome to Neuvii!

Your account has been created successfully. Here are your login details:

Email: {user.email}
Temporary Password: {temp_password}

Please click the link below to set your new password:
{reset_link}

Alternatively, you can login at: http://127.0.0.1:8000/auth/login/

IMPORTANT: You will be required to change your password upon first login for security reasons.

If you have any questions, please contact our support team.

Best regards,
Neuvii Team
        """

        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Failed to send email: {e}")


# Custom admin site titles
admin.site.site_header = "Neuvii Administration"
admin.site.site_title = "Neuvii Admin Portal"
admin.site.index_title = "Welcome to Neuvii Administration"