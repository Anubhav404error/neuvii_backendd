from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from django.utils.http import urlencode
from .models import (
    ParentProfile, Child, SpeechArea, LongTermGoal, 
    ShortTermGoal, Task, Assignment, TherapistProfile
)
import json


@login_required
def assign_task_wizard(request):
    """Multi-step task assignment wizard for therapists"""
    parent_id = request.GET.get('parent_id')
    if not parent_id:
        messages.error(request, 'Parent ID is required')
        return redirect('/admin/therapy/parentprofile/')
    
    parent = get_object_or_404(ParentProfile, id=parent_id)
    
    # Verify therapist has access to this parent
    if not request.user.is_superuser:
        role = getattr(getattr(request.user, "role", None), "name", "").lower()
        if role == "therapist":
            therapist = TherapistProfile.objects.filter(email=request.user.email).first()
            if not therapist or parent.assigned_therapist != therapist:
                messages.error(request, 'You do not have permission to assign tasks to this client')
                return redirect('/admin/therapy/parentprofile/')
    
    # Get children for this parent
    children = parent.children.all()
    speech_areas = SpeechArea.objects.filter(is_active=True)
    
    context = {
        'parent': parent,
        'children': children,
        'speech_areas': speech_areas,
    }
    
    return render(request, 'therapy/assign_task_wizard.html', context)


@login_required
@require_http_methods(["GET"])
def get_long_term_goals(request):
    """AJAX endpoint to get long-term goals for a speech area"""
    speech_area_id = request.GET.get('speech_area_id')
    if not speech_area_id:
        return JsonResponse({'goals': []})
    
    goals = LongTermGoal.objects.filter(
        speech_area_id=speech_area_id, 
        is_active=True
    ).values('id', 'title')
    
    return JsonResponse({'goals': list(goals)})


@login_required
@require_http_methods(["GET"])
def get_short_term_goals(request):
    """AJAX endpoint to get short-term goals for a long-term goal"""
    long_term_goal_id = request.GET.get('long_term_goal_id')
    if not long_term_goal_id:
        return JsonResponse({'goals': []})
    
    goals = ShortTermGoal.objects.filter(
        long_term_goal_id=long_term_goal_id, 
        is_active=True
    ).values('id', 'title')
    
    return JsonResponse({'goals': list(goals)})


@login_required
@require_http_methods(["GET"])
def get_tasks(request):
    """AJAX endpoint to get tasks for a short-term goal"""
    short_term_goal_id = request.GET.get('short_term_goal_id')
    if not short_term_goal_id:
        return JsonResponse({'tasks': []})
    
    tasks = Task.objects.filter(
        short_term_goal_id=short_term_goal_id, 
        is_active=True
    ).values('id', 'title', 'description', 'difficulty')
    
    return JsonResponse({'tasks': list(tasks)})


@login_required
@require_http_methods(["POST"])
def assign_tasks(request):
    """Process task assignment"""
    try:
        data = json.loads(request.body)
        parent_id = data.get('parent_id')
        selected_tasks = data.get('selected_tasks', [])
        
        if not all([parent_id, selected_tasks]):
            return JsonResponse({'success': False, 'error': 'Missing required data'})
        
        parent = get_object_or_404(ParentProfile, id=parent_id)
        
        # Get the first child for this parent (or you can modify this logic)
        child = parent.children.first()
        if not child:
            return JsonResponse({'success': False, 'error': 'No child found for this parent'})
        
        # Get therapist
        therapist = TherapistProfile.objects.filter(email=request.user.email).first()
        if not therapist:
            return JsonResponse({'success': False, 'error': 'Therapist profile not found'})
        
        # Verify access
        if not request.user.is_superuser and parent.assigned_therapist != therapist:
            return JsonResponse({'success': False, 'error': 'Permission denied'})
        
        # Create assignments
        assignments_created = 0
        child_name = child.name
        for task_id in selected_tasks:
            task = get_object_or_404(Task, id=task_id)
            
            # Check if assignment already exists
            if not Assignment.objects.filter(child=child, task=task, therapist=therapist).exists():
                Assignment.objects.create(
                    child=child,
                    task=task,
                    therapist=therapist
                )
                assignments_created += 1
        
        return JsonResponse({
            'success': True, 
            'message': f'{assignments_created} tasks assigned successfully to {child_name}',
            'child_name': child_name,
            'redirect_url': '/admin/therapy/parentprofile/'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})