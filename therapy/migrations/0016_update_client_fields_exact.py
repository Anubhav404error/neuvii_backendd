"""
# Update ClientProfile to match exact form fields from screenshot

1. Model Updates
   - Update ClientProfile to have exactly the fields shown in the form
   - First Name and Last Name are for the child (not parent)
   - Parent Email ID for parent contact
   - FSCD ID for administrative purposes
   - Assign Therapist dropdown
   - Date of Birth for the child

2. Field Mapping
   - First Name → child_first_name
   - Last Name → child_last_name  
   - Parent Email ID → parent_email
   - FSCD ID → fscd_id
   - Assign Therapist → assigned_therapist
   - Date of Birth → child_date_of_birth

3. Remove Unnecessary Fields
   - Remove all fields not shown in the form
   - Keep only the 6 fields visible in the screenshot
"""

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('therapy', '0015_migrate_legacy_data'),
    ]

    operations = [
        # Remove all unnecessary fields not shown in the form
        migrations.RemoveField(
            model_name='clientprofile',
            name='parent_first_name',
        ),
        migrations.RemoveField(
            model_name='clientprofile',
            name='parent_last_name',
        ),
        migrations.RemoveField(
            model_name='clientprofile',
            name='parent_phone',
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
            name='child_first_name',
            field=models.CharField(max_length=255, verbose_name="First Name"),
        ),
        migrations.AlterField(
            model_name='clientprofile',
            name='child_last_name',
            field=models.CharField(max_length=255, verbose_name="Last Name"),
        ),
        migrations.AlterField(
            model_name='clientprofile',
            name='parent_email',
            field=models.EmailField(verbose_name="Parent Email ID"),
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
    ]