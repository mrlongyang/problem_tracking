# core/management/commands/createsuperuser.py

from django.core.management.base import BaseCommand
from core.models import User, Department

class Command(BaseCommand):
    help = 'Create a superuser with department manually'

    def handle(self, *args, **kwargs):
        department, _ = Department.objects.get_or_create(department_name="Admin")
        user = User.objects.create_superuser(
            user_id="01669",
            email="longyang@mail.com",
            name="longyang",
            department=department,
            password="472001"
        )
        print("✅ Superuser created:", user.email)