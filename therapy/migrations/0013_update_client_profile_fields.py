"""
# Update ClientProfile with complete field set

1. Model Updates
   - Add missing fields to ClientProfile model to match the form requirements
   - Add proper field labels and help text
   - Ensure all fields from the "Add New Client" form are included

2. Data Migration
   - Preserve existing ClientProfile data
   - Update field constraints and validation

3. Admin Interface
   - Update admin interface to show only ClientProfile (not Child)
   - Implement proper field organization and validation
"""

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('therapy', '0012_create_client_profile'),
    ]

    operations = [
        # Update ClientProfile model with additional fields
        migrations.AlterField(
            model_name='clientprofile',
            name='parent_first_name',
            field=models.CharField(max_length=255, verbose_name="First Name", help_text="Parent's first name"),
        ),
        migrations.AlterField(
            model_name='clientprofile',
            name='parent_last_name',
            field=models.CharField(max_length=255, verbose_name="Last Name", help_text="Parent's last name"),
        ),
        migrations.AlterField(
            model_name='clientprofile',
            name='parent_email',
            field=models.EmailField(max_length=254, verbose_name="Parent Email ID", help_text="Email for parent login and notifications"),
        ),
        migrations.AlterField(
            model_name='clientprofile',
            name='child_date_of_birth',
            field=models.DateField(verbose_name="Date of Birth", help_text="Child's date of birth"),
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
                verbose_name="Assign Therapist",
                help_text="Therapist assigned to this client"
            ),
        ),
        
        # Make clinic field required for proper data organization
        migrations.AlterField(
            model_name='clientprofile',
            name='clinic',
            field=models.ForeignKey(
                'clinic.Clinic',
                on_delete=models.CASCADE,
                verbose_name="Clinic"
            ),
        ),
    ]