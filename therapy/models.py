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

# Unified Client Profile (matches form fields exactly)
class ClientProfile(models.Model):
    # Parent Information (from form)
    parent_first_name = models.CharField(max_length=255, verbose_name="First Name")
    parent_last_name = models.CharField(max_length=255, verbose_name="Last Name")
    parent_email = models.EmailField(verbose_name="Parent Email ID")
    
    # Child Information (from form)
    child_first_name = models.CharField(max_length=255, verbose_name="Child Name")
    child_date_of_birth = models.DateField(verbose_name="Date of Birth")
    
    # Administrative Information (from form)
    fscd_id = models.CharField(max_length=50, verbose_name="FSCD ID")
    
    # Assignment Information (from form)
    assigned_therapist = models.ForeignKey(
        TherapistProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_clients',
        verbose_name="Assign Therapist"
    )
    
    # System fields
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    date_added = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        verbose_name = 'Client'
        verbose_name_plural = 'Clients'
        ordering = ['parent_last_name', 'parent_first_name', 'child_first_name']

    def __str__(self):
        return f"{self.parent_first_name} {self.parent_last_name} (Child: {self.child_first_name})"
    
    @property
    def child_full_name(self):
        return self.child_first_name
    
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

# Goal model - unified with ClientProfile
class Goal(models.Model):
    client = models.ForeignKey(
        ClientProfile, 
        on_delete=models.CASCADE,
        related_name='goals'
    )
    title = models.CharField(max_length=255)
    is_long_term = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.client.child_full_name}"

class Task(models.Model):
    DIFFICULTY_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]
    
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE, related_name='tasks')
    title = models.TextField()
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Assignment(models.Model):
    client = models.ForeignKey(
        ClientProfile, 
        on_delete=models.CASCADE, 
        related_name='assignments'
    )
    therapist = models.ForeignKey(
        TherapistProfile, 
        on_delete=models.CASCADE, 
        related_name='assignments'
    )
    task = models.ForeignKey(
        Task, 
        on_delete=models.CASCADE, 
        related_name='assignments'
    )
    assigned_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField(null=True, blank=True)
    completed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.task.title} assigned to {self.client.child_full_name} by {self.therapist}"

    @property
    def client_name(self):
        return self.client.child_full_name


# Legacy models - kept for data migration but hidden from admin
class ParentProfile(models.Model):
    """DEPRECATED: Use ClientProfile instead - kept for data migration"""
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    parent_email = models.EmailField(blank=True, null=True)
    child_name = models.CharField(max_length=255, help_text="Child's full name")
    child_age = models.IntegerField(help_text="Child's age")
    child_gender = models.CharField(
        max_length=10, 
        choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')],
        help_text="Child's gender"
    )
    child_date_of_birth = models.DateField(blank=True, null=True, help_text="Child's date of birth")
    fscd_id = models.CharField(max_length=50, blank=True, null=True, help_text="FSCD ID number")
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
    """DEPRECATED: Use ClientProfile instead - kept for data migration"""
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
            pass

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
            pass