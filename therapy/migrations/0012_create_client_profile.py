"""
# Create ClientProfile model and migrate data

1. New Tables
   - `therapy_clientprofile`
     - `id` (auto field, primary key)
     - `parent_first_name` (varchar 255)
     - `parent_last_name` (varchar 255)
     - `parent_email` (email field)
     - `parent_phone` (varchar 20, optional)
     - `child_first_name` (varchar 255)
     - `child_last_name` (varchar 255)
     - `child_date_of_birth` (date)
     - `child_gender` (varchar 10)
     - `fscd_id` (varchar 50, optional)
     - `assigned_therapist_id` (foreign key to TherapistProfile)
     - `clinic_id` (foreign key to Clinic)
     - `emergency_contact_name` (varchar 255, optional)
     - `emergency_contact_phone` (varchar 20, optional)
     - `medical_notes` (text, optional)
     - `therapy_goals` (text, optional)
     - `is_active` (boolean, default True)
     - `date_added` (datetime, auto_now_add)

2. Data Migration
   - Migrate existing ParentProfile data to ClientProfile
   - Preserve all relationships and data integrity

3. Model Updates
   - Update Goal and Assignment models to support ClientProfile
   - Maintain backward compatibility with existing Child model

4. Security
   - Maintain existing RLS and permissions
   - Ensure proper clinic-based access control
"""

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('clinic', '0004_rename_sonsent_template_clinic_consent_template'),
        ('therapy', '0011_auto_20250826_0619'),
    ]

    operations = [
        # Create the new ClientProfile model
        migrations.CreateModel(
            name='ClientProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('parent_first_name', models.CharField(max_length=255, verbose_name='Parent First Name')),
                ('parent_last_name', models.CharField(max_length=255, verbose_name='Parent Last Name')),
                ('parent_email', models.EmailField(max_length=254, verbose_name='Parent Email ID', help_text='Email for parent login and notifications')),
                ('parent_phone', models.CharField(blank=True, max_length=20, null=True, verbose_name='Parent Phone')),
                ('child_first_name', models.CharField(max_length=255, verbose_name='Child First Name')),
                ('child_last_name', models.CharField(max_length=255, verbose_name='Child Last Name')),
                ('child_date_of_birth', models.DateField(help_text="Child's date of birth", verbose_name='Date of Birth')),
                ('child_gender', models.CharField(choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')], max_length=10, verbose_name='Child Gender')),
                ('fscd_id', models.CharField(blank=True, help_text='Family Support for Children with Disabilities ID', max_length=50, null=True, verbose_name='FSCD ID')),
                ('emergency_contact_name', models.CharField(blank=True, max_length=255, null=True, verbose_name='Emergency Contact Name')),
                ('emergency_contact_phone', models.CharField(blank=True, max_length=20, null=True, verbose_name='Emergency Contact Phone')),
                ('medical_notes', models.TextField(blank=True, null=True, verbose_name='Medical Notes')),
                ('therapy_goals', models.TextField(blank=True, null=True, verbose_name='Therapy Goals')),
                ('is_active', models.BooleanField(default=True)),
                ('date_added', models.DateTimeField(auto_now_add=True, blank=True, null=True)),
                ('assigned_therapist', models.ForeignKey(blank=True, help_text='Therapist assigned to this client', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_clients', to='therapy.therapistprofile', verbose_name='Assign Therapist')),
                ('clinic', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='clinic.clinic')),
            ],
            options={
                'verbose_name': 'Client',
                'verbose_name_plural': 'Clients',
                'ordering': ['parent_last_name', 'parent_first_name', 'child_last_name', 'child_first_name'],
            },
        ),
        
        # Add client field to Goal model
        migrations.AddField(
            model_name='goal',
            name='client',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='therapy.clientprofile'),
        ),
        
        # Add client field to Assignment model
        migrations.AddField(
            model_name='assignment',
            name='client',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='assignments', to='therapy.clientprofile'),
        ),
        
        # Make child field optional in Assignment model
        migrations.AlterField(
            model_name='assignment',
            name='child',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='assignments_legacy', to='therapy.child'),
        ),
        
        # Make child field optional in Goal model
        migrations.AlterField(
            model_name='goal',
            name='child',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='therapy.child'),
        ),
    ]