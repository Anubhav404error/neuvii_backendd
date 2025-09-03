from django.db import models
from django.conf import settings
from django.db.models.signals import post_delete
from django.db.models.signals import post_save
from django.dispatch import receiver
from clinic.models import Clinic


# Speech Area Model
class SpeechArea(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name


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


# Long-Term Goal Model
class LongTermGoal(models.Model):
    speech_area = models.ForeignKey(SpeechArea, on_delete=models.CASCADE, related_name='long_term_goals')
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.speech_area.name}: {self.title}"


# Short-Term Goal Model  
class ShortTermGoal(models.Model):
    long_term_goal = models.ForeignKey(LongTermGoal, on_delete=models.CASCADE, related_name='short_term_goals')
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.long_term_goal.speech_area.name}: {self.title}"


# Task Model (updated)
class Task(models.Model):
    short_term_goal = models.ForeignKey(ShortTermGoal, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True, null=True)
    difficulty = models.CharField(
        max_length=20,
        choices=[('beginner', 'Beginner'), ('intermediate', 'Intermediate'), ('advanced', 'Advanced')],
        default='beginner'
    )
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.short_term_goal.long_term_goal.speech_area.name}: {self.title}"


# Parent Profile (Client)
class ParentProfile(models.Model):
    FSCD_CHOICES = [
        ('approve', 'Approve'),
        ('reject', 'Reject'),
    ]
    AGE_CHOICES = [(i, str(i)) for i in range(1, 101)]  # 1–100 dropdown

    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    parent_email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE, null=True, blank=True)
    date_added = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    # ✅ New required fields
    age = models.IntegerField(choices=AGE_CHOICES, null=True, blank=True)
    fscd_approval = models.CharField(max_length=10, choices=FSCD_CHOICES, default='approve')

    assigned_therapist = models.ForeignKey(
        'therapy.TherapistProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_clients'
    )

    class Meta:
        verbose_name = 'Client'
        verbose_name_plural = 'Clients'

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


# Child Model
class Child(models.Model):
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
        related_name='children'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        clinic_name = self.clinic.name if self.clinic else "No Clinic"
        return f"{self.name} ({clinic_name})"


class Assignment(models.Model):
    child = models.ForeignKey("Child", on_delete=models.CASCADE, related_name="assignments")
    therapist = models.ForeignKey(TherapistProfile, on_delete=models.CASCADE, related_name='assignments')
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='assignments')
    assigned_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField(null=True, blank=True)
    completed = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.task.title} assigned to {self.child.name} by {self.therapist.first_name}"


# Signal handlers to auto-delete User accounts when profiles are deleted
@receiver(post_delete, sender=TherapistProfile)
def delete_therapist_user(sender, instance, **kwargs):
    if instance.email:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            user = User.objects.get(email=instance.email)
            user.delete()
        except User.DoesNotExist:
            pass


# Signal to create user when ParentProfile is created
@receiver(post_save, sender=ParentProfile)
def create_parent_user(sender, instance, created, **kwargs):
    """Create user account when ParentProfile is created"""
    if created and instance.parent_email and instance.first_name:
        from users.utils import create_user_with_role
        create_user_with_role(
            email=instance.parent_email,
            first_name=instance.first_name,
            last_name=instance.last_name or "",
            role_name="parent",
            send_credentials=True
        )


# Signal to create user when TherapistProfile is created
@receiver(post_save, sender=TherapistProfile)
def create_therapist_user(sender, instance, created, **kwargs):
    """Create user account when TherapistProfile is created"""
    if created and instance.email and instance.first_name:
        from users.utils import create_user_with_role
        create_user_with_role(
            email=instance.email,
            first_name=instance.first_name,
            last_name=instance.last_name or "",
            role_name="therapist",
            send_credentials=True
        )
@receiver(post_delete, sender=ParentProfile)
def delete_parent_user(sender, instance, **kwargs):
    if instance.parent_email:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            user = User.objects.get(email=instance.parent_email)
            user.delete()
        except User.DoesNotExist:
            pass
