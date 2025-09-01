from django.core.management.base import BaseCommand
from users.models import Role


class Command(BaseCommand):
    help = 'Create default roles for the application'

    def handle(self, *args, **options):
        roles = [
            'clinic admin',
            'therapist', 
            'parent',
            'super admin'
        ]
        
        created_count = 0
        for role_name in roles:
            role, created = Role.objects.get_or_create(name=role_name)
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully created role: {role_name}')
                )
            else:
                self.stdout.write(f'Role already exists: {role_name}')
        
        if created_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'\nCreated {created_count} new roles')
            )
        else:
            self.stdout.write('All roles already exist')
