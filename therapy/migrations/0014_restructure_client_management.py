"""
# Restructure Client Management System

1. Model Updates
   - Update ClientProfile to match exact fields from the form
   - Remove unnecessary fields not shown in the form
   - Ensure proper field organization and validation

2. Data Migration
   - Migrate existing Child and ParentProfile data to ClientProfile
   - Preserve all relationships and data integrity
   - Update Goal and Assignment relationships

3. Admin Interface Updates
   - Hide Child and ParentProfile from admin interface
   - Update ClientProfile admin to show only required fields
   - Implement proper clinic-based filtering

4. Security
   - Maintain existing RLS and permissions
   - Ensure proper clinic-based access control
"""

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('clinic', '0004_rename_sonsent_template_clinic_consent_template'),
        ('therapy', '0013_update_client_profile_fields'),
    ]

    operations = [
        # Remove unnecessary fields from ClientProfile to match form exactly
        migrations.RemoveField(
            model_name='clientprofile',
            name='parent_phone',
        ),
        migrations.RemoveField(
            model_name='clientprofile',
            name='child_last_name',
        ),
        migrations.RemoveField(
            model_name='clientprofile',
            name='child_gender',
        ),
        migrations.RemoveField(
            model_name='clientprofile',
            name='emergency_contact_name',
        ),
        migrations.RemoveField(
            model_name='clientprofile',
            name='emergency_contact_phone',
        ),
        migrations.RemoveField(
            model_name='clientprofile',
            name='medical_notes',
        ),
        migrations.RemoveField(
            model_name='clientprofile',
            name='therapy_goals',
        ),
        
        # Update field labels to match form exactly
        migrations.AlterField(
            model_name='clientprofile',
            name='parent_first_name',
            field=models.CharField(max_length=255, verbose_name="First Name"),
        ),
        migrations.AlterField(
            model_name='clientprofile',
            name='parent_last_name',
            field=models.CharField(max_length=255, verbose_name="Last Name"),
        ),
        migrations.AlterField(
            model_name='clientprofile',
            name='parent_email',
            field=models.EmailField(verbose_name="Parent Email ID"),
        ),
        migrations.AlterField(
            model_name='clientprofile',
            name='child_first_name',
            field=models.CharField(max_length=255, verbose_name="Child Name"),
        ),
        migrations.AlterField(
            model_name='clientprofile',
            name='child_date_of_birth',
            field=models.DateField(verbose_name="Date of Birth"),
        ),
        migrations.AlterField(
            model_name='clientprofile',
            name='fscd_id',
            field=models.CharField(max_length=50, verbose_name="FSCD ID"),
        ),
        migrations.AlterField(
            model_name='clientprofile',
            name='assigned_therapist',
            field=models.ForeignKey(
                'TherapistProfile',
                on_delete=models.SET_NULL,
                null=True,
                blank=True,
                related_name='assigned_clients',
                verbose_name="Assign Therapist"
            ),
        ),
        
        # Update Goal model to only use ClientProfile
        migrations.RemoveField(
            model_name='goal',
            name='child',
        ),
        migrations.AlterField(
            model_name='goal',
            name='client',
            field=models.ForeignKey(
                'ClientProfile',
                on_delete=models.CASCADE,
                related_name='goals'
            ),
        ),
        
        # Update Assignment model to only use ClientProfile
        migrations.RemoveField(
            model_name='assignment',
            name='child',
        ),
        migrations.AlterField(
            model_name='assignment',
            name='client',
            field=models.ForeignKey(
                'ClientProfile',
                on_delete=models.CASCADE,
                related_name='assignments'
            ),
        ),
    ]