from .models import Problem

def problem_notifications(request):
    if request.user.is_authenticated:
        unresolved_count = Problem.objects.exclude(status__in=['Closed', 'Resolved ✅']).count()
    else:
        unresolved_count = 0
    return {
        'notification_count': unresolved_count
    }
