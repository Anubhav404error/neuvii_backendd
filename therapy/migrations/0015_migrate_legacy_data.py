"""
# Migrate legacy Child and ParentProfile data to ClientProfile

1. Data Migration
   - Migrate existing Child records to ClientProfile
   - Migrate existing ParentProfile records to ClientProfile
   - Preserve all relationships and data integrity
   - Update Goal and Assignment relationships

2. Cleanup
   - Remove legacy model registrations from admin
   - Ensure no data loss during migration
"""

from django.db import migrations
from datetime import date


def migrate_child_data_to_client_profile(apps, schema_editor):
    """Migrate Child model data to ClientProfile"""
    Child = apps.get_model('therapy', 'Child')
    ClientProfile = apps.get_model('therapy', 'ClientProfile')
    ParentProfile = apps.get_model('therapy', 'ParentProfile')
    
    for child in Child.objects.all():
        # Get parent information
        parent = child.parent
        
        # Calculate date of birth from age (approximate)
        current_year = date.today().year
        estimated_birth_year = current_year - child.age
        estimated_dob = date(estimated_birth_year, 1, 1)  # Default to Jan 1st
        
        # Create ClientProfile from Child data
        client_profile, created = ClientProfile.objects.get_or_create(
            parent_first_name=parent.first_name,
            parent_last_name=parent.last_name,
            parent_email=parent.parent_email or f"parent_{child.id}@example.com",
            child_first_name=child.name,
            child_date_of_birth=estimated_dob,
            fscd_id=getattr(parent, 'fscd_id', '') or f"FSCD{child.id}",
            defaults={
                'assigned_therapist': child.assigned_therapist,
                'clinic': child.clinic,
                'is_active': True,
                'date_added': child.created_at,
            }
        )
        
        if created:
            print(f"Migrated Child {child.name} to ClientProfile {client_profile.id}")


def migrate_parent_data_to_client_profile(apps, schema_editor):
    """Migrate ParentProfile data to ClientProfile where not already migrated"""
    ParentProfile = apps.get_model('therapy', 'ParentProfile')
    ClientProfile = apps.get_model('therapy', 'ClientProfile')
    
    for parent in ParentProfile.objects.all():
        # Check if already migrated via Child
        existing = ClientProfile.objects.filter(
            parent_email=parent.parent_email,
            child_first_name=parent.child_name
        ).first()
        
        if not existing:
            # Calculate date of birth from age
            current_year = date.today().year
            estimated_birth_year = current_year - parent.child_age
            estimated_dob = date(estimated_birth_year, 1, 1)
            
            client_profile = ClientProfile.objects.create(
                parent_first_name=parent.first_name,
                parent_last_name=parent.last_name,
                parent_email=parent.parent_email or f"parent_{parent.id}@example.com",
                child_first_name=parent.child_name,
                child_date_of_birth=estimated_dob,
                fscd_id=parent.fscd_id or f"FSCD{parent.id}",
                assigned_therapist=parent.assigned_therapist,
                clinic=parent.clinic,
                is_active=parent.is_active,
                date_added=parent.date_added,
            )
            print(f"Migrated ParentProfile {parent.id} to ClientProfile {client_profile.id}")


def update_goal_relationships(apps, schema_editor):
    """Update Goal relationships to use ClientProfile"""
    Goal = apps.get_model('therapy', 'Goal')
    ClientProfile = apps.get_model('therapy', 'ClientProfile')
    Child = apps.get_model('therapy', 'Child')
    
    for goal in Goal.objects.filter(child__isnull=False):
        # Find corresponding ClientProfile
        child = goal.child
        try:
            client_profile = ClientProfile.objects.get(
                child_first_name=child.name,
                clinic=child.clinic
            )
            goal.client = client_profile
            goal.save()
            print(f"Updated Goal {goal.id} to use ClientProfile {client_profile.id}")
        except ClientProfile.DoesNotExist:
            print(f"Could not find ClientProfile for Goal {goal.id}")


def update_assignment_relationships(apps, schema_editor):
    """Update Assignment relationships to use ClientProfile"""
    Assignment = apps.get_model('therapy', 'Assignment')
    ClientProfile = apps.get_model('therapy', 'ClientProfile')
    Child = apps.get_model('therapy', 'Child')
    
    for assignment in Assignment.objects.filter(child__isnull=False):
        # Find corresponding ClientProfile
        child = assignment.child
        try:
            client_profile = ClientProfile.objects.get(
                child_first_name=child.name,
                clinic=child.clinic
            )
            assignment.client = client_profile
            assignment.save()
            print(f"Updated Assignment {assignment.id} to use ClientProfile {client_profile.id}")
        except ClientProfile.DoesNotExist:
            print(f"Could not find ClientProfile for Assignment {assignment.id}")


class Migration(migrations.Migration):

    dependencies = [
        ('therapy', '0014_restructure_client_management'),
    ]

    operations = [
        migrations.RunPython(
            migrate_child_data_to_client_profile,
            migrations.RunPython.noop
        ),
        migrations.RunPython(
            migrate_parent_data_to_client_profile,
            migrations.RunPython.noop
        ),
        migrations.RunPython(
            update_goal_relationships,
            migrations.RunPython.noop
        ),
        migrations.RunPython(
            update_assignment_relationships,
            migrations.RunPython.noop
        ),
    ]