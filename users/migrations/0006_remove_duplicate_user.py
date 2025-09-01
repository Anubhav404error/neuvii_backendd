from django.db import migrations


def remove_duplicate_user(apps, schema_editor):
    User = apps.get_model('users', 'User')
    # Find users with duplicate email
    duplicate_email = 'adititomar201098@gmail.com'
    users = User.objects.filter(email=duplicate_email).order_by('id')
    
    # Keep the first user with names and delete the rest
    if users.count() > 1:
        # Delete the first user (ID 1) which has empty names
        users.first().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_remove_duplicate_user'),
    ]

    operations = [
        migrations.RunPython(remove_duplicate_user, migrations.RunPython.noop),
    ]
