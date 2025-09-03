# Automatic User Creation System

## Overview
The system now automatically creates users with appropriate roles when adding new clinics, therapists, or parents through the admin interface.

## How It Works

### 1. Clinic Admin Creation
- When adding a new **Clinic** with `contact_person_name` and `email`
- Automatically creates a user with role **"clinic admin"**
- Uses contact person name for first/last name
- Sends welcome email with temporary password

### 2. Therapist User Creation  
- When adding a new **TherapistProfile** with `first_name`, `last_name`, and `email`
- Automatically creates a user with role **"therapist"**
- Sends welcome email with temporary password

### 3. Parent User Creation
- When adding a new **ParentProfile** with `first_name`, `last_name`, and `parent_email`
- Automatically creates a user with role **"parent"**
- Sends welcome email with temporary password

## Required Setup

### 1. Create Default Roles
Run this command to create the required roles:
```bash
python manage.py create_default_roles
```

### 2. Email Configuration
Ensure your Django settings have email configured for sending welcome emails.

## Features

- **Duplicate Prevention**: Won't create duplicate users if email already exists
- **Automatic Password Generation**: Creates secure temporary passwords
- **Email Notifications**: Sends welcome emails with login credentials
- **Role-based Access**: Assigns appropriate permissions based on role
- **Admin Feedback**: Shows success/warning messages in admin interface

## Email Template
Users receive emails with:
- Temporary login credentials
- Password reset link
- Role information
- Login instructions

## Security
- Users must reset password on first login
- Temporary passwords are securely generated
- Email verification required for password reset
