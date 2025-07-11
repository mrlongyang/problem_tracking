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
    unresolved_count = 0
    latest_problem_link = ''
    
    if request.user.is_authenticated:
        unresolved = Problem.objects.exclude(status__in=['Closed', 'Resolved ✅']).order_by('-created_at')
        unresolved_count = unresolved.count()
        if unresolved.exists():
            latest_problem_link = reverse('problem_detail', kwargs={'problem_id': unresolved.first().problem_id})

    return {
    'notification_count': unresolved_count,
    'latest_problem_link': latest_problem_link
    }