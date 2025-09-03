from django.core.management.base import BaseCommand
from therapy.models import SpeechArea, LongTermGoal, ShortTermGoal, Task


class Command(BaseCommand):
    help = 'Populate speech areas, goals, and tasks with sample data'

    def handle(self, *args, **options):
        self.stdout.write('Creating speech areas, goals, and tasks...')
        
        # Create Speech Areas
        speech_areas_data = [
            {
                'name': 'Expressive Language',
                'description': 'Developing skills to express thoughts, ideas, and needs verbally'
            },
            {
                'name': 'Receptive Language', 
                'description': 'Understanding and processing spoken language and instructions'
            },
            {
                'name': 'Social Communication / Pragmatics',
                'description': 'Learning appropriate social communication skills and conversation rules'
            },
            {
                'name': 'Speech Sounds / Articulation',
                'description': 'Improving pronunciation and clarity of speech sounds'
            }
        ]
        
        for area_data in speech_areas_data:
            area, created = SpeechArea.objects.get_or_create(
                name=area_data['name'],
                defaults={'description': area_data['description']}
            )
            if created:
                self.stdout.write(f'Created speech area: {area.name}')
        
        # Create Long-Term Goals for Expressive Language
        expressive_lang = SpeechArea.objects.get(name='Expressive Language')
        long_term_goals_expressive = [
            'Child will use age-appropriate vocabulary to express needs, wants, and ideas.',
            'Child will follow multi-step directions.',
            'Child will produce age-appropriate target sounds.',
            'Child will initiate and maintain conversational exchanges.'
        ]
        
        for goal_title in long_term_goals_expressive:
            goal, created = LongTermGoal.objects.get_or_create(
                speech_area=expressive_lang,
                title=goal_title
            )
            if created:
                self.stdout.write(f'Created long-term goal: {goal_title[:50]}...')
        
        # Create Short-Term Goals for first long-term goal
        first_long_term = LongTermGoal.objects.filter(speech_area=expressive_lang).first()
        if first_long_term:
            short_term_goals = [
                'Child will ask/answer peer questions.',
                'Child will end conversations appropriately.',
                'Child will follow 2-step directions with objects.',
                'Child will follow 3-step unrelated directions.',
                'Child will follow classroom/group instructions.',
                'Child will follow conditional directions.',
                'Child will generalize sound into conversation.',
                'Child will initiate greetings.',
                'Child will label 20+ common objects.',
                'Child will maintain topic for 3 turns.',
                'Child will name 20+ actions (verbs).',
                'Child will produce sound in isolation.',
                'Child will produce sound in sentences.',
                'Child will produce sound in words (initial/medial/final).',
                'Child will use descriptive words (colors, size, feelings).',
                'Child will use new words weekly in functional contexts.'
            ]
            
            for goal_title in short_term_goals:
                goal, created = ShortTermGoal.objects.get_or_create(
                    long_term_goal=first_long_term,
                    title=goal_title
                )
                if created:
                    self.stdout.write(f'Created short-term goal: {goal_title[:50]}...')
        
        # Create Tasks for some short-term goals
        sample_tasks = [
            {
                'title': 'Pick up pencil and give to me.',
                'difficulty': 'beginner'
            },
            {
                'title': 'Pick red block then sit down.',
                'difficulty': 'beginner'
            },
            {
                'title': 'Get book, open it, put on desk.',
                'difficulty': 'intermediate'
            },
            {
                'title': 'Clap, touch nose, jump.',
                'difficulty': 'beginner'
            },
            {
                'title': 'Clap, spin, tap table.',
                'difficulty': 'intermediate'
            },
            {
                'title': 'Open door, pick ball, put in basket.',
                'difficulty': 'intermediate'
            },
            {
                'title': 'Line up and get backpack.',
                'difficulty': 'beginner'
            },
            {
                'title': 'Get paper, write name, hand in.',
                'difficulty': 'advanced'
            },
            {
                'title': 'Finish worksheet, put away, start activity.',
                'difficulty': 'advanced'
            }
        ]
        
        # Add tasks to the first few short-term goals
        short_term_goals = ShortTermGoal.objects.filter(long_term_goal=first_long_term)[:3]
        
        for i, short_term_goal in enumerate(short_term_goals):
            # Add 3 tasks per short-term goal
            start_idx = i * 3
            end_idx = start_idx + 3
            
            for task_data in sample_tasks[start_idx:end_idx]:
                if start_idx < len(sample_tasks):
                    task, created = Task.objects.get_or_create(
                        short_term_goal=short_term_goal,
                        title=task_data['title'],
                        defaults={'difficulty': task_data['difficulty']}
                    )
                    if created:
                        self.stdout.write(f'Created task: {task.title[:50]}...')
        
        self.stdout.write(self.style.SUCCESS('Successfully populated speech data!'))