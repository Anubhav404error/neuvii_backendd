from django.contrib import admin
from django.contrib.admin import AdminSite
from django.urls import path
from django.shortcuts import redirect


class NeuviiAdminSite(AdminSite):
    """Custom admin site for Neuvii with role-based access"""
    site_header = "Neuvii Administration"
    site_title = "Neuvii Admin Portal"
    index_title = "Welcome to Neuvii Administration"

    def has_permission(self, request):
        """
        Return True if the given HttpRequest has permission to view
        *at least one* page in the admin site.
        """
        # Superuser always has permission
        if request.user.is_superuser:
            return True
        return request.user.is_active and request.user.is_staff

    def get_app_list(self, request, app_label=None):
        """Customize app list based on user role"""
        app_list = super().get_app_list(request, app_label)
        
        # Superuser sees only Clinic Management
        if request.user.is_superuser:
            filtered_apps = []
            for app in app_list:
                if app['app_label'] == 'clinic':
                    app['name'] = 'Clinic Management'
                    filtered_apps.append(app)
            return filtered_apps
        
        if not hasattr(request.user, 'role') or not request.user.role:
            return []
            
        user_role = request.user.role.name.lower()
        
        if user_role == 'clinic admin':
            # Clinic admin sees their profile, Client Management and Therapy Management
            filtered_apps = []
            for app in app_list:
                if app['app_label'] == 'clinic':
                    app['name'] = 'My Clinic Profile'
                    filtered_apps.append(app)
                elif app['app_label'] == 'therapy':
                    # Split therapy app into sections
                    client_models = []
                    therapy_models = []
                    
                    for model in app['models']:
                        if model['object_name'] == 'ClientProfile':
                            model['name'] = 'Clients'
                            client_models.append(model)
                        elif model['object_name'] == 'TherapistProfile':
                            model['name'] = 'Therapists'
                            therapy_models.append(model)
                    
                    # Create Client Management section
                    if client_models:
                        client_app = {
                            'name': 'Client Management',
                            'app_label': 'client_management',
                            'app_url': '/admin/therapy/',
                            'has_module_perms': True,
                            'models': client_models
                        }
                        filtered_apps.append(client_app)
                    
                    # Create Therapy Management section
                    if therapy_models:
                        therapy_app = {
                            'name': 'Therapy Management',
                            'app_label': 'therapy_management',
                            'app_url': '/admin/therapy/',
                            'has_module_perms': True,
                            'models': therapy_models
                        }
                        filtered_apps.append(therapy_app)
                        
                elif app['app_label'] == 'users':
                    app['name'] = 'User Management'
                    filtered_apps.append(app)
                    
            return filtered_apps
            
        elif user_role == 'therapist':
            filtered_apps = []
            for app in app_list:
                if app['app_label'] == 'therapy':
                    profile_models = []
                    assignment_models = []
                    
                    for model in app['models']:
                        if model['object_name'] == 'TherapistProfile':
                            model['name'] = 'My Profile'
                            profile_models.append(model)
                        elif model['object_name'] == 'ClientProfile':
                            model['name'] = 'My Clients'
                            assignment_models.append(model)
                    
                    # Create My Profile section
                    if profile_models:
                        profile_app = {
                            'name': 'My Profile',
                            'app_label': 'therapist_profile',
                            'app_url': '/admin/therapy/',
                            'has_module_perms': True,
                            'models': profile_models
                        }
                        filtered_apps.append(profile_app)
                    
                    # Create My Assignments section
                    if assignment_models:
                        assignment_app = {
                            'name': 'My Assignments',
                            'app_label': 'therapist_assignments',
                            'app_url': '/admin/therapy/',
                            'has_module_perms': True,
                            'models': assignment_models
                        }
                        filtered_apps.append(assignment_app)
            return filtered_apps
        
        elif user_role == 'parent':
            filtered_apps = []
            for app in app_list:
                if app['app_label'] == 'therapy':
                    client_models = []
                    
                    for model in app['models']:
                        if model['object_name'] == 'ClientProfile':
                            model['name'] = 'My Child Profile'
                            client_models.append(model)
                    
                    # Create My Child Profile section
                    if client_models:
                        client_app = {
                            'name': 'My Child Profile',
                            'app_label': 'parent_client',
                            'app_url': '/admin/therapy/',
                            'has_module_perms': True,
                            'models': client_models
                        }
                        filtered_apps.append(client_app)
            return filtered_apps
        
        return []


# Create the custom admin site instance
neuvii_admin_site = NeuviiAdminSite(name='neuvii_admin')