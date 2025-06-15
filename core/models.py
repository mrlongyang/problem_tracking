from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.conf import settings
import uuid


class Department(models.Model):
    department_id = models.CharField(max_length=10, primary_key=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class UserGroup(models.Model):
    user_group_id = models.CharField(primary_key=True, max_length=20)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class User(AbstractBaseUser, PermissionsMixin):
    user_group = models.ForeignKey(UserGroup, on_delete=models.SET_NULL, null=True, blank=True)
    user_id = models.CharField(primary_key=True, max_length=50, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    role = models.CharField(max_length=10, choices=[('admin', 'Admin'), ('user', 'User'), ('staff', 'Staff')])
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    def __str__(self):
        return self.email


class Problem(models.Model):
    problem_id = models.AutoField(primary_key=True) 
    PRIORITY = [('Low', 'Low'), ('Medium', 'Medium'), ('High', 'High'), ('Critical', 'Critical')]
    STATUS = [('Open', 'Open'), ('In Progress', 'In Progress'), ('Solved', 'Solved'), ('Closed', 'Closed')]
    title = models.CharField(max_length=255)
    description = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    user_group = models.ForeignKey(UserGroup, on_delete=models.SET_NULL, null=True, blank=True)  
    priority = models.CharField(max_length=10, choices=PRIORITY)
    status = models.CharField(max_length=15, choices=STATUS, default='Open')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class ProblemAttachment(models.Model):
    problemattachment_id = models.CharField(primary_key=True, max_length=50)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    file = models.FileField(upload_to='attachments/')
    file_type = models.CharField(max_length=50)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Attachment for {self.problem.title}"

class Solution(models.Model):
    solution_id = models.CharField(primary_key=True, max_length=50)
    problem = models.ForeignKey('Problem', on_delete=models.CASCADE, related_name='solutions')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    content = models.TextField()
    is_final_solution = models.BooleanField(default=False)
    solution_type = models.CharField(
        max_length=30,
        choices=[
            ('text', 'Text Explanation'),
            ('code', 'Code Fix'),
            ('config', 'Configuration Change'),
            ('workaround', 'Workaround'),
            ('documentation', 'Documentation Link'),
        ],
        default='text'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.solution_type} solution for problem #{self.problem_id}"


class SolutionAttachment(models.Model):
    solution = models.ForeignKey(Solution, on_delete=models.CASCADE, related_name='attachments')
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    file = models.FileField(upload_to='solution_attachments/', null=True, blank=True)
    link = models.URLField(null=True, blank=True)
    file_type = models.CharField(
        max_length=20,
        choices=[
            ('file', 'File'),
            ('image', 'Image'),
            ('link', 'Link'),
        ]
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Attachment for Solution #{self.solution.id} ({self.file_type})"


class Tag(models.Model):
    name = models.CharField(max_length=50)

class ProblemTag(models.Model):
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)

