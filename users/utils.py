from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from .models import User, Role


def create_user_with_role(email, first_name, last_name, role_name, request=None, send_credentials=True):
    """
    Utility function to automatically create a user with specified role
    and send welcome email with temporary password.
    
    Args:
        email (str): User's email address
        first_name (str): User's first name
        last_name (str): User's last name
        role_name (str): Role name (e.g., 'clinic admin', 'therapist', 'parent')
        request: Django request object for admin messages (optional)
        send_credentials (bool): Whether to send credentials even for existing users
    
    Returns:
        User: Created user object or existing user if email already exists
    """
    
    # Check if user already exists
    if User.objects.filter(email=email).exists():
        existing_user = User.objects.get(email=email)
        
        # Update role if different
        try:
            role = Role.objects.get(name__iexact=role_name)
            if existing_user.role != role:
                existing_user.role = role
                existing_user.save(update_fields=['role'])
                # Update permissions for the new role
                assign_role_permissions(existing_user, role_name)
        except Role.DoesNotExist:
            pass
        
        if send_credentials:
            # Generate new temporary password for existing user
            temp_password = existing_user.generate_temp_password()
            existing_user.password_reset_required = True
            existing_user.save(update_fields=['password', 'password_reset_required'])
            
            # Send credentials email
            send_welcome_email(existing_user, temp_password, role_name)
            
            if request:
                messages.success(
                    request, 
                    f'User {existing_user.get_full_name()} already exists. New login credentials sent to {email}.'
                )
        else:
            if request:
                messages.warning(
                    request, 
                    f'User with email {email} already exists. Using existing user: {existing_user.get_full_name()}'
                )
        
        return existing_user
    
    try:
        # Get the role
        role = Role.objects.get(name__iexact=role_name)
    except Role.DoesNotExist:
        if request:
            messages.error(
                request,
                f'Role "{role_name}" does not exist. Please create this role first.'
            )
        return None
    
    # Create new user with staff permissions for admin access
    user = User.objects.create(
        email=email,
        first_name=first_name,
        last_name=last_name,
        role=role,
        is_active=True,
        is_staff=True,  # Required for admin access
        password_reset_required=True
    )
    
    # Generate temporary password
    temp_password = user.generate_temp_password()
    user.save()
    
    # Assign role-based permissions
    assign_role_permissions(user, role_name)
    
    # Send welcome email
    send_welcome_email(user, temp_password, role_name)
    
    if request:
        messages.success(
            request,
            f'User {user.get_full_name()} ({email}) created successfully as {role_name}. Welcome email sent with temporary password.'
        )
    
    return user


def assign_role_permissions(user, role_name):
    """
    Assign specific permissions to user based on their role
    
    Args:
        user: User object
        role_name: Role name (e.g., 'clinic admin', 'therapist', 'parent')
    """
    role_name_lower = role_name.lower()
    
    # Clear existing permissions
    user.user_permissions.clear()
    
    if role_name_lower == 'clinic admin':
        # Clinic Admin permissions - full access to clinic-related models
        permissions = [
            # Clinic permissions
            'clinic.add_clinic', 'clinic.change_clinic', 'clinic.view_clinic',
            # Therapist permissions
            'therapy.add_therapistprofile', 'therapy.change_therapistprofile', 
            'therapy.view_therapistprofile', 'therapy.delete_therapistprofile',
            # Parent/Client permissions
            'therapy.add_parentprofile', 'therapy.change_parentprofile', 
            'therapy.view_parentprofile', 'therapy.delete_parentprofile',
            # Child permissions
            'therapy.add_child', 'therapy.change_child', 'therapy.view_child',
            # Assignment permissions
            'therapy.add_assignment', 'therapy.change_assignment', 'therapy.view_assignment',
            # Goal and Task permissions
            'therapy.add_goal', 'therapy.change_goal', 'therapy.view_goal',
            'therapy.add_task', 'therapy.change_task', 'therapy.view_task',
        ]
        
    elif role_name_lower == 'therapist':
        # Therapist permissions - limited to their assigned cases
        permissions = [
            # View clinic info
            'clinic.view_clinic',
            # Parent/Client permissions
            'therapy.add_parentprofile', 'therapy.change_parentprofile', 
            'therapy.view_parentprofile',
            # Child permissions
            'therapy.add_child', 'therapy.change_child', 'therapy.view_child',
            # Assignment permissions
            'therapy.add_assignment', 'therapy.change_assignment', 'therapy.view_assignment',
            # Goal and Task permissions
            'therapy.add_goal', 'therapy.change_goal', 'therapy.view_goal',
            'therapy.add_task', 'therapy.change_task', 'therapy.view_task',
            # View their own profile
            'therapy.view_therapistprofile', 'therapy.change_therapistprofile',
        ]
        
    elif role_name_lower == 'parent':
        # Parent permissions - very limited, mainly view their child's info
        permissions = [
            # View their child's information
            'therapy.view_child',
            # View assignments for their child
            'therapy.view_assignment',
            # View goals and tasks for their child
            'therapy.view_goal', 'therapy.view_task',
            # View and update their own profile
            'therapy.view_parentprofile', 'therapy.change_parentprofile',
        ]
        
    else:
        # Default permissions for unknown roles
        permissions = ['clinic.view_clinic']
    
    # Assign permissions to user
    for perm_codename in permissions:
        try:
            app_label, codename = perm_codename.split('.')
            permission = Permission.objects.get(
                content_type__app_label=app_label,
                codename=codename
            )
            user.user_permissions.add(permission)
        except Permission.DoesNotExist:
            print(f"Permission {perm_codename} does not exist")
            continue
    
    print(f"Assigned {len(permissions)} permissions to {user.email} as {role_name}")


def send_welcome_email(user, temp_password, role_name):
    """Send welcome email with temporary password"""
    subject = f'Welcome to Neuvii - Your {role_name.title()} Account'
    
    # Create password reset link
    reset_link = f"http://127.0.0.1:8000/auth/reset-password/?email={user.email}&temp_password={temp_password}"
    
    message = f"""
Welcome to Neuvii!

Your {role_name} account has been created successfully. Here are your login details:

Email: {user.email}
Temporary Password: {temp_password}
Role: {role_name.title()}

Please click the link below to set your new password:
{reset_link}

Alternatively, you can login at: http://127.0.0.1:8000/auth/login/

IMPORTANT: You will be required to change your password upon first login for security reasons.

If you have any questions, please contact our support team.

Best regards,
Neuvii Team
    """
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
    except Exception as e:
        print(f"Failed to send email to {user.email}: {e}")


def parse_contact_person_name(contact_person_name):
    """
    Parse contact person name into first_name and last_name
    
    Args:
        contact_person_name (str): Full name string
        
    Returns:
        tuple: (first_name, last_name)
    """
    if not contact_person_name:
        return "", ""
    
    name_parts = contact_person_name.strip().split()
    
    if len(name_parts) == 1:
        return name_parts[0], ""
    elif len(name_parts) >= 2:
        first_name = name_parts[0]
        last_name = " ".join(name_parts[1:])
        return first_name, last_name
    
    return "", ""
