from django.contrib import admin
from django import forms
from django.contrib.auth.models import Permission
from django.urls import reverse
from django.utils.html import format_html
from django.utils.http import urlencode
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth import get_user_model

from neuvii_backend.admin_sites import neuvii_admin_site
from .models import TherapistProfile, ParentProfile, Child, Assignment
from users.models import Role
from users.utils import create_user_with_role

User = get_user_model()

# ==========
# Utilities
# ==========
def _role_name(user):
    return getattr(getattr(user, "role", None), "name", "").lower()


# ===========================
# Therapist Profile Admin
# ===========================
class TherapistProfileForm(forms.ModelForm):
    class Meta:
        model = TherapistProfile
        fields = "__all__"
        widgets = {"date_added": forms.DateInput(attrs={"type": "date"})}


@admin.register(TherapistProfile, site=neuvii_admin_site)
class TherapistProfileAdmin(admin.ModelAdmin):
    form = TherapistProfileForm
    list_display = ["id", "first_name", "last_name", "email", "phone_number", "is_active", "date_added"]
    search_fields = ["first_name", "last_name", "email", "phone_number"]
    list_filter = ["is_active", "date_added"]
    exclude = ["clinic"]
    readonly_fields = ["date_added"]

    # Scope visible rows
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        role = _role_name(request.user)
        if request.user.is_superuser:
            return qs
        if role == "therapist":
            return qs.filter(email=request.user.email)
        if role == "clinic admin":
            from clinic.models import Clinic
            try:
                clinic = Clinic.objects.get(clinic_admin=request.user)
                return qs.filter(clinic=clinic)
            except Clinic.DoesNotExist:
                return qs.none()
        return qs.none()

    # Restrict who can change/add/delete
    def has_add_permission(self, request):
        return _role_name(request.user) in ("clinic admin",) or request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        role = _role_name(request.user)
        if request.user.is_superuser:
            return True
        if role == "therapist":
            # Therapist can edit ONLY their own profile
            return obj is None or (obj and obj.email == request.user.email)
        if role == "clinic admin":
            return True
        return False

    def has_delete_permission(self, request, obj=None):
        role = _role_name(request.user)
        return role == "clinic admin" or request.user.is_superuser

    # Auto-attach clinic for clinic admin creating therapist
    def save_model(self, request, obj, form, change):
        role = _role_name(request.user)
        if not change and role == "clinic admin":
            from clinic.models import Clinic
            try:
                clinic = Clinic.objects.get(clinic_admin=request.user)
                obj.clinic = clinic
            except Clinic.DoesNotExist:
                pass
        super().save_model(request, obj, form, change)

        # Create linked user on first save
        if obj.first_name and obj.email and not change:
            create_user_with_role(
                email=obj.email,
                first_name=obj.first_name,
                last_name=obj.last_name or "",
                role_name="therapist",
                request=request,
            )


# ===========================
# Parent (Client) Admin
# ===========================
class ParentProfileForm(forms.ModelForm):
    class Meta:
        model = ParentProfile
        fields = [
            "first_name", "last_name", "parent_email", "phone_number",
            "age", "fscd_approval", "assigned_therapist"
        ]

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)
        # Limit therapist choices for clinic admin; superuser sees all
        if self.request:
            role = _role_name(self.request.user)
            if role == "clinic admin":
                from clinic.models import Clinic
                try:
                    clinic = Clinic.objects.get(clinic_admin=self.request.user)
                    self.fields["assigned_therapist"].queryset = TherapistProfile.objects.filter(clinic=clinic)
                except Clinic.DoesNotExist:
                    self.fields["assigned_therapist"].queryset = TherapistProfile.objects.none()
            elif self.request.user.is_superuser:
                self.fields["assigned_therapist"].queryset = TherapistProfile.objects.all()


@admin.register(ParentProfile, site=neuvii_admin_site)
class ParentProfileAdmin(admin.ModelAdmin):
    form = ParentProfileForm
    list_display = [
        "id", "first_name", "last_name", "parent_email", "phone_number",
        "age", "fscd_approval", "assigned_therapist", "clinic", "date_added", "is_active",
        "add_tasks_button"
    ]
    search_fields = ["first_name", "last_name", "parent_email", "phone_number"]
    list_filter = ["clinic", "fscd_approval", "is_active"]
    readonly_fields = ["date_added"]

    # “Add Tasks” button on the changelist (rightmost column)
    def add_tasks_button(self, obj):
        url = (
            reverse("neuvii_admin:therapy_assignment_add")
            + "?"
            + urlencode({"parent_id": obj.pk})
        )
        return format_html('<a class="button" href="{}" style="float:right;">Add Tasks</a>', url)
    add_tasks_button.short_description = "Add Tasks"
    add_tasks_button.allow_tags = True

    # Provide request to form
    def get_form(self, request, obj=None, **kwargs):
        kwargs["form"] = self.form
        form = super().get_form(request, obj, **kwargs)
        form.request = request
        return form

    # Scope rows by role
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        role = _role_name(request.user)
        if request.user.is_superuser:
            return qs
        if role == "parent":
            return qs.filter(parent_email=request.user.email)
        if role == "therapist":
            return qs.filter(assigned_therapist__email=request.user.email)
        if role == "clinic admin":
            from clinic.models import Clinic
            try:
                clinic = Clinic.objects.get(clinic_admin=request.user)
                return qs.filter(clinic=clinic)
            except Clinic.DoesNotExist:
                return qs.none()
        return qs.none()

    # Permissions:
    # Parent -> edit own profile only
    # Therapist -> view only
    # Clinic admin -> full (for their clinic)
    def has_add_permission(self, request):
        role = _role_name(request.user)
        return role in ("clinic admin",) or request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        role = _role_name(request.user)
        if request.user.is_superuser:
            return True
        if role == "parent":
            return obj is None or (obj and obj.parent_email == request.user.email)
        if role == "therapist":
            return False  # view-only
        if role == "clinic admin":
            return True
        return False

    def has_delete_permission(self, request, obj=None):
        role = _role_name(request.user)
        return role == "clinic admin" or request.user.is_superuser

    # Auto-attach clinic on create by clinic admin; create linked user for parent
    def save_model(self, request, obj, form, change):
        role = _role_name(request.user)
        if not change and role == "clinic admin":
            from clinic.models import Clinic
            try:
                clinic = Clinic.objects.get(clinic_admin=request.user)
                obj.clinic = clinic
            except Clinic.DoesNotExist:
                pass

        super().save_model(request, obj, form, change)

        # Ensure a staff User exists for parent with correct perms to view their profile/assignments
        if obj.parent_email:
            user, created = User.objects.get_or_create(
                email=obj.parent_email,
                defaults={"is_active": True, "is_staff": True},
            )
            role_parent = Role.objects.filter(name__iexact="parent").first()
            if role_parent:
                user.role = role_parent
            try:
                view_parent_perm = Permission.objects.get(codename="view_parentprofile")
                view_assignment_perm = Permission.objects.get(codename="view_assignment")
                user.user_permissions.add(view_parent_perm, view_assignment_perm)
            except Permission.DoesNotExist:
                pass
            user.is_staff = True
            user.is_active = True
            user.save()


# ===========================
# Assignment Admin (Tasks)
# ===========================
@admin.register(Assignment, site=neuvii_admin_site)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ["id", "task", "child", "therapist", "assigned_date", "due_date", "completed"]
    search_fields = ["task__title", "child__name", "therapist__first_name", "therapist__last_name"]
    list_filter = ["completed", "due_date"]

    # Scope visible rows by role
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        role = _role_name(request.user)
        if request.user.is_superuser:
            return qs
        if role == "parent":
            return qs.filter(child__parent__parent_email=request.user.email)
        if role == "therapist":
            # Tasks assigned by this therapist (their workload)
            return qs.filter(therapist__email=request.user.email)
        if role == "clinic admin":
            # Clinic admin CANNOT see assignments
            return qs.none()
        return qs.none()

    # Limit FK choices based on role and GET params (parent_id or child_id)
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        role = _role_name(request.user)

        # Pre-filter children for therapist
        if db_field.name == "child":
            parent_id = request.GET.get("parent_id")
            child_id = request.GET.get("child_id")
            qs = Child.objects.all()

            if role == "therapist":
                qs = qs.filter(assigned_therapist__email=request.user.email)
                if parent_id:
                    qs = qs.filter(parent_id=parent_id)
                if child_id:
                    qs = qs.filter(pk=child_id)
                kwargs["queryset"] = qs

            elif role == "parent":
                # Parent should never add; but for safety, limit to their children
                qs = qs.filter(parent__parent_email=request.user.email)
                kwargs["queryset"] = qs

        # Therapist field: auto restrict to self for therapist
        if db_field.name == "therapist":
            if role == "therapist":
                kwargs["queryset"] = TherapistProfile.objects.filter(email=request.user.email)

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    # Default initial values (therapist = current therapist)
    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        role = _role_name(request.user)
        if role == "therapist":
            tp = TherapistProfile.objects.filter(email=request.user.email).first()
            if tp:
                initial["therapist"] = tp.pk
        return initial

    # Permissions:
    # - Therapist: full (add/change/delete/view) BUT only for their own assignments
    # - Parent: view only
    # - Clinic admin: no access (hidden by menu and permissions)
    def has_module_permission(self, request):
        role = _role_name(request.user)
        if request.user.is_superuser:
            return True
        if role in ("therapist", "parent"):
            return True
        return False

    def has_add_permission(self, request):
        role = _role_name(request.user)
        return request.user.is_superuser or role == "therapist"

    def has_change_permission(self, request, obj=None):
        role = _role_name(request.user)
        if request.user.is_superuser:
            return True
        if role == "therapist":
            # Therapists can edit only assignments they own
            return obj is None or (obj and obj.therapist and obj.therapist.email == request.user.email)
        if role == "parent":
            return False
        return False

    def has_delete_permission(self, request, obj=None):
        role = _role_name(request.user)
        if request.user.is_superuser:
            return True
        if role == "therapist":
            return obj is None or (obj and obj.therapist and obj.therapist.email == request.user.email)
        return False
