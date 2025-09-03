"""
URL configuration for neuvii_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from .admin_sites import neuvii_admin_site

def redirect_to_login(request):
    return redirect('/auth/login/')

# Custom admin site header
admin.site.site_header = 'Neuvii Administration'
admin.site.site_title = 'Neuvii Administration'
admin.site.index_title = 'Site Administration'

urlpatterns = [
    path("admin/", neuvii_admin_site.urls),
    path("auth/", include('users.urls')),
    path("therapy/", include('therapy.urls')),
    path('', redirect_to_login),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)