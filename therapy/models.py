from django.db import models
from django.conf import settings
from django.db.models.signals import post_delete
from django.dispatch import receiver
from clinic.models import Clinic

# Therapist Profile
class TherapistProfile(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True, blank=True, null=True)
    phone_number = models.CharField(max_length=100, blank=True, null=True)
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    date_added = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        verbose_name = 'Therapist'
        verbose_name_plural = 'Therapists'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

# Enhanced Client Profile (combining Parent and Child information)
class ClientProfile(models.Model):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]

    # Parent Information
    parent_first_name = models.CharField(max_length=255, verbose_name="Parent First Name")
    parent_last_name = models.CharField(max_length=255, verbose_name="Parent Last Name")
    parent_email = models.EmailField(verbose_name="Parent Email ID", help_text="Email for parent login and notifications")
    parent_phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Parent Phone")
    
    # Child Information
    child_first_name = models.CharField(max_length=255, verbose_name="Child First Name")
    child_last_name = models.CharField(max_length=255, verbose_name="Child Last Name")
    child_date_of_birth = models.DateField(verbose_name="Date of Birth", help_text="Child's date of birth")
    child_gender = models.CharField(
        max_length=10, 
        choices=GENDER_CHOICES,
        verbose_name="Child Gender"
    )
    
    # Administrative Information
    fscd_id = models.CharField(max_length=50, blank=True, null=True, verbose_name="FSCD ID", help_text="Family Support for Children with Disabilities ID")
    
    # Assignment Information
    assigned_therapist = models.ForeignKey(
        TherapistProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_clients',
        verbose_name="Assign Therapist"
    )
    
    # Clinic and Status
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    date_added = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    
    # Additional fields for comprehensive client management
    emergency_contact_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Emergency Contact Name")
    emergency_contact_phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Emergency Contact Phone")
    medical_notes = models.TextField(blank=True, null=True, verbose_name="Medical Notes")
    therapy_goals = models.TextField(blank=True, null=True, verbose_name="Therapy Goals")

    class Meta:
        verbose_name = 'Client'
        verbose_name_plural = 'Clients'
        ordering = ['parent_last_name', 'parent_first_name', 'child_last_name', 'child_first_name']

    def __str__(self):
        return f"{self.parent_first_name} {self.parent_last_name} (Child: {self.child_first_name} {self.child_last_name})"
    
    @property
    def child_full_name(self):
        return f"{self.child_first_name} {self.child_last_name}"
    
    @property
    def parent_full_name(self):
        return f"{self.parent_first_name} {self.parent_last_name}"
    
    @property
    def child_age(self):
        """Calculate child's current age from date of birth"""
        if self.child_date_of_birth:
            from datetime import date
            today = date.today()
            return today.year - self.child_date_of_birth.year - ((today.month, today.day) < (self.child_date_of_birth.month, self.child_date_of_birth.day))
        return None

# Keep legacy models for backward compatibility but mark as deprecated
class ParentProfile(models.Model):
    """DEPRECATED: Use ClientProfile instead"""
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    parent_email = models.EmailField(blank=True, null=True)
    
    # Child information fields (merged from Child model)
    child_name = models.CharField(max_length=255, help_text="Child's full name")
    child_age = models.IntegerField(help_text="Child's age")
    child_gender = models.CharField(
        max_length=10, 
        choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')],
        help_text="Child's gender"
    )
    child_date_of_birth = models.DateField(blank=True, null=True, help_text="Child's date of birth")
    fscd_id = models.CharField(max_length=50, blank=True, null=True, help_text="FSCD ID number")
    
    # Assignment information
    assigned_therapist = models.ForeignKey(
        'TherapistProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_clients_legacy',
        help_text="Therapist assigned to this client"
    )
    
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE, null=True, blank=True)
    date_added = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Client (Legacy)'
        verbose_name_plural = 'Clients (Legacy)'

    def __str__(self):
        return f"{self.first_name} {self.last_name} (Child: {self.child_name})"

class Child(models.Model):
    """DEPRECATED: Use ClientProfile instead"""
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]

    name = models.CharField(max_length=255)
    age = models.IntegerField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE)
    parent = models.ForeignKey(
        ParentProfile,
        on_delete=models.CASCADE,
        related_name='children'
    )
    assigned_therapist = models.ForeignKey(
        TherapistProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children_legacy'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Child (Legacy)'
        verbose_name_plural = 'Children (Legacy)'

    def __str__(self):
        clinic_name = self.clinic.name if self.clinic else "No Clinic"
        return f"{self.name} ({clinic_name})"

class Goal(models.Model):
    # Support both legacy Child and new ClientProfile
    child = models.ForeignKey(Child, on_delete=models.CASCADE, null=True, blank=True)
    client = models.ForeignKey(ClientProfile, on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=255)
    is_long_term = models.BooleanField(default=False)

    def __str__(self):
        if self.client:
            return f"{self.title} - {self.client.child_full_name}"
        elif self.child:
            return f"{self.title} - {self.child.name}"
        return self.title

class Task(models.Model):
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE)
    title = models.TextField()
    difficulty = models.CharField(max_length=20, choices=[('beginner', 'Beginner'), ('intermediate', 'Intermediate'), ('advanced', 'Advanced')])

    def __str__(self):
        return self.title

class Assignment(models.Model):
    # Support both legacy Child and new ClientProfile
    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name='assignments_legacy', null=True, blank=True)
    client = models.ForeignKey(ClientProfile, on_delete=models.CASCADE, related_name='assignments', null=True, blank=True)
    therapist = models.ForeignKey(TherapistProfile, on_delete=models.CASCADE, related_name='assignments')
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='assignments')
    assigned_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField(null=True, blank=True)
    completed = models.BooleanField(default=False)

    def __str__(self):
        if self.client:
            return f"{self.task.title} assigned to {self.client.child_full_name} by {self.therapist}"
        elif self.child:
            return f"{self.task.title} assigned to {self.child.name} by {self.therapist}"
        return f"{self.task.title} assignment"

    @property
    def client_name(self):
        if self.client:
            return self.client.child_full_name
        elif self.child:
            return self.child.name
        return "Unknown"


# Signal handlers to auto-delete User accounts when profiles are deleted
@receiver(post_delete, sender=TherapistProfile)
def delete_therapist_user(sender, instance, **kwargs):
    """Delete User account when TherapistProfile is deleted"""
    if instance.email:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            user = User.objects.get(email=instance.email)
            user.delete()
        except User.DoesNotExist:
            pass  # User doesn't exist, nothing to delete


@receiver(post_delete, sender=ClientProfile)
def delete_client_user(sender, instance, **kwargs):
    """Delete User account when ClientProfile is deleted"""
    if instance.parent_email:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            user = User.objects.get(email=instance.parent_email)
            user.delete()
        except User.DoesNotExist:
            pass  # User doesn't exist, nothing to delete


@receiver(post_delete, sender=ParentProfile)
def delete_parent_user(sender, instance, **kwargs):
    """Delete User account when ParentProfile is deleted (legacy)"""
    if instance.parent_email:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            user = User.objects.get(email=instance.parent_email)
            user.delete()
        except User.DoesNotExist:
            pass  # User doesn't exist, nothing to delete