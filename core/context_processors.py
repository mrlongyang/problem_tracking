from .models import Problem
from django.urls import reverse

def problem_notifications(request):
    if request.user.is_authenticated:
        unresolved_count = Problem.objects.exclude(status__in=['Closed', 'Resolved ✅']).count()
    else:
        unresolved_count = 0
    return {
        'notification_count': unresolved_count
    }

def problem_notification(request):
    if request.user.is_authenticated:
        unresolved = Problem.objects.exclude(status__in=['Closed', 'Resolved ✅']).order_by('-created_at')
        count = unresolved.count()

        if unresolved.exists():
            first_problem = unresolved.first()
            problem_url = reverse('problem_detail', kwargs={'pk': first_problem.pk})
        else:
            problem_url = reverse('problem_list')  # fallback

        return {
            'notification_count': count,
            'notification_url': problem_url
        }
    return {
        'notification_count': 0,
        'notification_url': reverse('problem_list')
    }
