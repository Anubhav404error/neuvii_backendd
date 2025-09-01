from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.http import HttpResponseRedirect
from django.urls import reverse
from .forms import LoginForm, PasswordResetForm
from .models import User


@csrf_protect
@never_cache
def login_view(request):
    """Custom login view that handles role-based redirection"""
    if request.user.is_authenticated:
        return redirect_to_dashboard(request.user)

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            user = authenticate(request, username=email, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)

                    # Check if password reset is required
                    if user.password_reset_required:
                        return redirect('reset_password')

                    return redirect_to_dashboard(user)
                else:
                    messages.error(request, 'Your account is disabled.')
            else:
                messages.error(request, 'Invalid email or password.')
    else:
        form = LoginForm()

    return render(request, 'auth/login.html', {'form': form})


def redirect_to_dashboard(user):
    """Redirect user to appropriate dashboard based on their role"""
    # Check if user has admin access
    if not user.is_staff:
        # If user doesn't have staff permissions, they can't access admin
        # For now, redirect to login with an error message
        from django.contrib import messages
        messages.error(None, 'You do not have permission to access the admin interface.')
        return redirect('/auth/login/')
    
    if not user.role:
        return redirect('/admin/')  # Default admin if no role

    role_name = user.role.name.lower().replace(' ', '_')

    # Define role-based redirections - all roles go to admin for now
    role_redirects = {
        'neuvii_admin': '/admin/',
        'clinic_admin': '/admin/',
        'therapist': '/admin/',
        'parent': '/admin/',
    }

    return redirect(role_redirects.get(role_name, '/admin/'))


def reset_password_view(request):
    """View to handle password reset for new users"""
    # Check if user is already logged in - redirect to change password instead
    if request.user.is_authenticated:
        return redirect('change_password')
    
    # Always get email and temp_password from GET parameters first
    email = request.GET.get('email')
    temp_password = request.GET.get('temp_password')
    
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            # Get email and temp_password from POST data (hidden fields) or fallback to GET
            post_email = request.POST.get('email')
            post_temp_password = request.POST.get('temp_password')
            new_password = form.cleaned_data['new_password']

            # Use POST values if available, otherwise use GET values
            final_email = post_email or email
            final_temp_password = post_temp_password or temp_password
            
            # Fix URL encoding and whitespace issues in email
            if final_email:
                # Replace spaces with + signs and remove all whitespace characters
                final_email = final_email.replace(' ', '+').replace('\n', '').replace('\r', '').replace('\t', '').strip()

            # Debug logging
            print(f"DEBUG: GET email: '{email}'")
            print(f"DEBUG: GET temp_password: '{temp_password}'")
            print(f"DEBUG: POST email: '{post_email}'")
            print(f"DEBUG: POST temp_password: '{post_temp_password}'")
            print(f"DEBUG: Final email: '{final_email}'")
            print(f"DEBUG: Final temp_password: '{final_temp_password}'")
            print(f"DEBUG: All POST data: {dict(request.POST)}")

            if not final_email:
                messages.error(request, 'Email parameter is missing.')
                return render(request, 'auth/reset_password.html', {
                    'form': PasswordResetForm(),
                    'email': email,
                    'temp_password': temp_password
                })

            try:
                user = User.objects.get(email=final_email)
                print(f"DEBUG: Found user: {user.email}")
                # Verify temp password
                if user.check_password(final_temp_password):
                    user.set_password(new_password)
                    user.password_reset_required = False
                    user.save()

                    # Auto login user
                    login(request, user)
                    messages.success(request, 'Password changed successfully!')
                    return redirect_to_dashboard(user)
                else:
                    messages.error(request, 'Invalid temporary password.')
            except User.DoesNotExist:
                # Try to find user with corrupted email (contains newlines/whitespace)
                try:
                    # Remove common email prefixes and search by partial match
                    email_base = final_email.replace('+', '').split('@')[0] if '@' in final_email else final_email
                    users_with_similar_email = User.objects.filter(email__icontains=email_base)
                    
                    print(f"DEBUG: Looking for users with email containing: '{email_base}'")
                    for u in users_with_similar_email:
                        clean_db_email = u.email.replace('\n', '').replace('\r', '').replace('\t', '').strip()
                        print(f"DEBUG: Checking user {u.id}: original='{u.email}', cleaned='{clean_db_email}'")
                        if clean_db_email == final_email:
                            print(f"DEBUG: Found matching user after cleaning: {u.email}")
                            user = u
                            # Verify temp password
                            if user.check_password(final_temp_password):
                                user.set_password(new_password)
                                user.password_reset_required = False
                                user.save()

                                # Auto login user
                                login(request, user)
                                messages.success(request, 'Password changed successfully!')
                                return redirect_to_dashboard(user)
                            else:
                                messages.error(request, 'Invalid temporary password.')
                            break
                    else:
                        print(f"DEBUG: No matching user found even with partial search")
                        messages.error(request, f'User not found with email: {final_email}')
                except Exception as e:
                    print(f"DEBUG: Error in partial search: {e}")
                    messages.error(request, f'User not found with email: {final_email}')
        else:
            print(f"DEBUG: Form is not valid. Errors: {form.errors}")
    else:
        form = PasswordResetForm()

    return render(request, 'auth/reset_password.html', {
        'form': form,
        'email': email,
        'temp_password': temp_password
    })


@login_required
def change_password_view(request):
    """View for users to change password after login"""
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['new_password']

            request.user.set_password(new_password)
            request.user.password_reset_required = False
            request.user.save()

            # Re-authenticate user with new password
            user = authenticate(request, username=request.user.email, password=new_password)
            login(request, user)

            messages.success(request, 'Password changed successfully!')
            return redirect_to_dashboard(request.user)
    else:
        form = PasswordResetForm()

    return render(request, 'auth/change_password.html', {'form': form})


def logout_view(request):
    """Handle user logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')