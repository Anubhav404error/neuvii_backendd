from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_POST
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
    if not parent_id or parent_id == 'all':
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
    
    # Get or create child for this parent
    children = parent.children.all()
    if not children.exists():
        # Auto-create child from parent profile
        child = Child.objects.create(
            name=f"{parent.first_name} {parent.last_name}",
            age=parent.age or 5,  # Default age if not specified
            gender='other',  # Default gender
            clinic=parent.clinic,
            parent=parent,
            assigned_therapist=parent.assigned_therapist
        )
        children = [child]
    
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
        
        # Get or create child for this parent
        child = parent.children.first()
        if not child:
            # Auto-create child from parent profile
            child = Child.objects.create(
                name=f"{parent.first_name} {parent.last_name}",
                age=parent.age or 5,  # Default age if not specified
                gender='other',  # Default gender
                clinic=parent.clinic,
                parent=parent,
                assigned_therapist=parent.assigned_therapist
            )
        
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


@login_required
@require_http_methods(["GET"])
def get_speech_areas(request):
    """AJAX endpoint to get all active speech areas"""
    speech_areas = SpeechArea.objects.filter(is_active=True).values('id', 'name', 'description')
    return JsonResponse({'speech_areas': list(speech_areas)})


@login_required
@require_POST
def create_speech_area(request):
    """Create a new speech area"""
    try:
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        
        if not name:
            return JsonResponse({'success': False, 'error': 'Name is required'})
        
        # Check if speech area already exists
        if SpeechArea.objects.filter(name__iexact=name).exists():
            return JsonResponse({'success': False, 'error': 'Speech area with this name already exists'})
        
        speech_area = SpeechArea.objects.create(
            name=name,
            description=description if description else None
        )
        
        return JsonResponse({
            'success': True,
            'speech_area': {
                'id': speech_area.id,
                'name': speech_area.name,
                'description': speech_area.description
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_POST
def create_long_term_goal(request):
    """Create a new long-term goal"""
    try:
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        speech_area_id = request.POST.get('speech_area_id')
        
        if not title:
            return JsonResponse({'success': False, 'error': 'Title is required'})
        
        if not speech_area_id:
            return JsonResponse({'success': False, 'error': 'Speech area is required'})
        
        speech_area = get_object_or_404(SpeechArea, id=speech_area_id)
        
        long_term_goal = LongTermGoal.objects.create(
            speech_area=speech_area,
            title=title,
            description=description if description else None
        )
        
        return JsonResponse({
            'success': True,
            'goal': {
                'id': long_term_goal.id,
                'title': long_term_goal.title,
                'description': long_term_goal.description
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_POST
def create_short_term_goal(request):
    """Create a new short-term goal"""
    try:
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        long_term_goal_id = request.POST.get('long_term_goal_id')
        
        if not title:
            return JsonResponse({'success': False, 'error': 'Title is required'})
        
        if not long_term_goal_id:
            return JsonResponse({'success': False, 'error': 'Long-term goal is required'})
        
        long_term_goal = get_object_or_404(LongTermGoal, id=long_term_goal_id)
        
        short_term_goal = ShortTermGoal.objects.create(
            long_term_goal=long_term_goal,
            title=title,
            description=description if description else None
        )
        
        return JsonResponse({
            'success': True,
            'goal': {
                'id': short_term_goal.id,
                'title': short_term_goal.title,
                'description': short_term_goal.description
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_POST
def create_task(request):
    """Create a new task"""
    try:
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        difficulty = request.POST.get('difficulty', '').strip()
        short_term_goal_id = request.POST.get('short_term_goal_id')
        
        if not title:
            return JsonResponse({'success': False, 'error': 'Title is required'})
        
        if not difficulty:
            return JsonResponse({'success': False, 'error': 'Difficulty is required'})
        
        if not short_term_goal_id:
            return JsonResponse({'success': False, 'error': 'Short-term goal is required'})
        
        if difficulty not in ['beginner', 'intermediate', 'advanced']:
            return JsonResponse({'success': False, 'error': 'Invalid difficulty level'})
        
        short_term_goal = get_object_or_404(ShortTermGoal, id=short_term_goal_id)
        
        task = Task.objects.create(
            short_term_goal=short_term_goal,
            title=title,
            description=description if description else None,
            difficulty=difficulty
        )
        
        return JsonResponse({
            'success': True,
            'task': {
                'id': task.id,
                'title': task.title,
                'description': task.description,
                'difficulty': task.difficulty
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})