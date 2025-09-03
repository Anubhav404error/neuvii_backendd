from django.contrib.admin import AdminSite


class NeuviiAdminSite(AdminSite):
    """Custom admin site for Neuvii with role-based access and custom menus"""
    site_header = "Neuvii Administration"
    site_title = "Neuvii Admin Portal"
    index_title = "Welcome to Neuvii Administration"

    def has_permission(self, request):
        # Allow superuser and any active staff to access admin
        if request.user.is_superuser:
            return True
        return request.user.is_active and request.user.is_staff

    def get_app_list(self, request, app_label=None):
        """
        Customize the left menu:
        - Parent:  My Information -> My Profile ; My Assignments -> Tasks
        - Therapist: My Information -> My Profile ; My Clients -> Clients ; My Assignments -> Tasks
        - Clinic Admin: manage clinic/therapists/clients only (NO assignments)
        """
        app_list = super().get_app_list(request, app_label)

        # Superuser: show "Clinic Management" app only (as in your original behavior)
        if request.user.is_superuser:
            filtered_apps = []
            for app in app_list:
                if app["app_label"] == "clinic":
                    app["name"] = "Clinic Management"
                    filtered_apps.append(app)
            return filtered_apps

        # No role? nothing
        role = getattr(getattr(request.user, "role", None), "name", None)
        if not role:
            return []

        user_role = role.lower()

        # ----------------------
        # Clinic Admin
        # ----------------------
        if user_role == "clinic admin":
            filtered_apps = []
            for app in app_list:
                if app["app_label"] == "clinic":
                    app["name"] = "My Clinic Profile"
                    filtered_apps.append(app)
                elif app["app_label"] == "therapy":
                    client_models, therapist_models = [], []
                    for m in app["models"]:
                        if m["object_name"] == "ParentProfile":
                            m["name"] = "Clients"
                            client_models.append(m)
                        elif m["object_name"] == "TherapistProfile":
                            m["name"] = "Therapists"
                            therapist_models.append(m)
                        # Explicitly skip Assignment for clinic admin
                    if client_models:
                        filtered_apps.append({
                            "name": "Client Management",
                            "app_label": "client_management",
                            "app_url": "/admin/therapy/",
                            "has_module_perms": True,
                            "models": client_models
                        })
                    if therapist_models:
                        filtered_apps.append({
                            "name": "Therapy Management",
                            "app_label": "therapy_management",
                            "app_url": "/admin/therapy/",
                            "has_module_perms": True,
                            "models": therapist_models
                        })
                elif app["app_label"] == "users":
                    app["name"] = "User Management"
                    filtered_apps.append(app)
            return filtered_apps

        # ----------------------
        # Therapist
        # ----------------------
        if user_role == "therapist":
            filtered_apps = []
            for app in app_list:
                if app["app_label"] == "therapy":
                    info_models, client_models, task_models = [], [], []
                    for m in app["models"]:
                        if m["object_name"] == "TherapistProfile":
                            m["name"] = "My Profile"
                            info_models.append(m)
                        elif m["object_name"] == "ParentProfile":
                            m["name"] = "Clients"
                            client_models.append(m)
                        elif m["object_name"] == "Assignment":
                            m["name"] = "Tasks"
                            task_models.append(m)
                    if info_models:
                        filtered_apps.append({
                            "name": "My Information",
                            "app_label": "therapist_info",
                            "app_url": "/admin/therapy/",
                            "has_module_perms": True,
                            "models": info_models
                        })
                    if client_models:
                        filtered_apps.append({
                            "name": "My Clients",
                            "app_label": "therapist_clients",
                            "app_url": "/admin/therapy/",
                            "has_module_perms": True,
                            "models": client_models
                        })
                    if task_models:
                        filtered_apps.append({
                            "name": "My Assignments",
                            "app_label": "therapist_tasks",
                            "app_url": "/admin/therapy/",
                            "has_module_perms": True,
                            "models": task_models
                        })
            return filtered_apps

        # ----------------------
        # Parent (Client)
        # ----------------------
        if user_role == "parent":
            filtered_apps = []
            for app in app_list:
                if app["app_label"] == "therapy":
                    info_models, task_models = [], []
                    for m in app["models"]:
                        if m["object_name"] == "ParentProfile":
                            m["name"] = "My Profile"
                            info_models.append(m)
                        elif m["object_name"] == "Assignment":
                            m["name"] = "Tasks"
                            task_models.append(m)
                    if info_models:
                        filtered_apps.append({
                            "name": "My Information",
                            "app_label": "parent_info",
                            "app_url": "/admin/therapy/",
                            "has_module_perms": True,
                            "models": info_models
                        })
                    if task_models:
                        filtered_apps.append({
                            "name": "My Assignments",
                            "app_label": "parent_tasks",
                            "app_url": "/admin/therapy/",
                            "has_module_perms": True,
                            "models": task_models
                        })
            return filtered_apps

        # Default: nothing
        return []


# Export the custom site
neuvii_admin_site = NeuviiAdminSite(name="neuvii_admin")
