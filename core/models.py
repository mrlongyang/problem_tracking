from django.db import models
from django.contrib.auth.models import AbstractBaseUser,BaseUserManager, PermissionsMixin
from django.conf import settings
from uuid import uuid4
import uuid
from django.db.models.aggregates import Count

class CustomUserManager(BaseUserManager):
    def create_user(self, user_id, email, name, password=None, **extra_fields):
        if not user_id:
            raise ValueError("Users must have a user_id")
        if not email:
            raise ValueError("Users must have an email")

        email = self.normalize_email(email)
        user = self.model(user_id=user_id, email=email, name=name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if not extra_fields.get('user_id'):
            extra_fields['user_id'] = 'admin001'  # or prompt to manually set
        return self.create_user(email, password, **extra_fields)



class Department(models.Model):
    department_id = models.CharField(max_length=10, primary_key=True)
    department_name = models.CharField(max_length=100)
    class Meta:
        verbose_name = "Department"              
        verbose_name_plural = "Department"

    def __str__(self):
        return self.department_name  
class UserManager(BaseUserManager):
    def generate_user_id(self, department):
        prefix = department.department_id.upper()  # e.g., HR
        count = User.objects.filter(department=department).count() + 1
        return f"{prefix}{count:03d}"  # e.g., HR001

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email must be set')
        email = self.normalize_email(email)
        department = extra_fields.get('department')
        if not department:
            raise ValueError('Department must be provided')
        if not extra_fields.get('user_id'):
            extra_fields['user_id'] = self.generate_user_id(department)
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
    usergroup_name = models.CharField(max_length=100)

    def __str__(self):
        return self.usergroup_name   
class Menu(models.Model):
    menu_id = models.CharField(primary_key=True, max_length=20)
    menu_name = models.CharField(max_length=100)
    nemu_url = models.CharField(max_length=200)
    class Meta:
        verbose_name = "Menu"              
        verbose_name_plural = "Menu"

    def __str__(self):
        return self.menu_name       

class Role(models.Model):
    role_id = models.CharField(max_length=20, primary_key=True)
    name = models.CharField(max_length=50)
    class Meta:
        verbose_name = "Role"              
        verbose_name_plural = "Role"

    def __str__(self):
        return self.name            
class Permission(models.Model):
    menu_id = models.ForeignKey(Menu, on_delete=models.CASCADE, related_name='permission')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, db_column='role_id')
    class Meta:
        unique_together = ('menu_id', 'role')
        constraints = [
            models.UniqueConstraint(fields=['menu_id', 'role'], name='unique_permission')
        ]
        verbose_name = "Permission"
        verbose_name_plural = "Permission"

    def __str__(self):
        return f"{self.role.name} can access {self.menu_id.menu_name}"

class User(AbstractBaseUser, PermissionsMixin):
    user_group = models.ForeignKey(UserGroup,on_delete=models.SET_NULL, null=True, blank=True)
    user_id = models.CharField(primary_key=True, max_length=255, unique=True)
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    objects = UserManager()

    USERNAME_FIELD = 'user_id'
    REQUIRED_FIELDS = ['email', 'name']

    def __str__(self):
        return self.email

class Module(models.Model):
    module_id = models.CharField(primary_key=True, max_length=20)
    module_name = models.CharField(max_length=100)

    class Meta:
        verbose_name = "Module"
        verbose_name_plural = "Module"

    def __str__(self):
        return self.module_name

class Problem(models.Model):
    PRIORITY = [
        ("Low", "Low"),
        ("Medium", "Medium"),
        ("High", "High"),
        ("Critical", "Critical"),
    ]

    STATUS = [
        ("Open", "Open"),
        ("Solved", "Solved"),
        ("Closed", "Closed"),
        ("Resolved", "Resolved"),
    ]

    SOURCE_TYPE = [
        ("manual", "Manual Entry"),
        ("word_import", "Word Import"),
        ("excel_import", "Excel Import"),
    ]

    problem_id = models.CharField(
        primary_key=True,
        max_length=50,
    )

    # Imported troubleshooting-guide information
    transaction_code = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        db_index=True,
        help_text="Example: 0015100",
    )

    error_code = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        db_index=True,
        help_text="Example: AI8808",
    )

    function_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Example: GL A/C Definition Maintenance",
    )

    source_type = models.CharField(
        max_length=20,
        choices=SOURCE_TYPE,
        default="manual",
    )

    source_file_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    status = models.CharField(
        max_length=15,
        choices=STATUS,
        default="Open",
    )

    title = models.CharField(max_length=255)

    description = models.TextField()
    
    module = models.ForeignKey(
        Module,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="problems",
)
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_problems",
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="problems",
    )

    user_group = models.ForeignKey(
        UserGroup,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="problems",
    )

    priority = models.CharField(
        max_length=10,
        choices=PRIORITY,
        default="Medium",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Problem"
        verbose_name_plural = "Problems"
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["error_code"]),
            models.Index(fields=["transaction_code"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        if self.error_code:
            return f"{self.error_code} - {self.title}"
        return f"{self.problem_id} - {self.title}"
    

class ProblemAttachment(models.Model):
    problemattachment_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    problem = models.ForeignKey(
        Problem,
        on_delete=models.CASCADE,
        related_name="attachments",
    )

    file = models.FileField(
        upload_to="attachments/%Y/%m/",
    )

    file_type = models.CharField(
        max_length=100,
        blank=True,
        default="",
    )

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Attachment for {self.problem.problem_id}"

class Solution(models.Model):
    SOLUTION_TYPES = [
        ("text", "Text Explanation"),
        ("code", "Code Fix"),
        ("config", "Configuration Change"),
        ("workaround", "Workaround"),
        ("documentation", "Documentation Link"),
        ("imported", "Imported Resolution"),
    ]

    solution_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    problem = models.ForeignKey(
        Problem,
        on_delete=models.CASCADE,
        related_name="solutions",
    )

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="solutions",
    )

    content = models.TextField()

    is_final_solution = models.BooleanField(default=False)

    solution_type = models.CharField(
        max_length=30,
        choices=SOLUTION_TYPES,
        default="text",
    )

    source_file_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Solution"
        verbose_name_plural = "Solutions"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.solution_type} solution for {self.problem.problem_id}"
    
class TroubleshootingImport(models.Model):
    STATUS_CHOICES = [
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("partial", "Completed With Errors"),
        ("failed", "Failed"),
    ]

    import_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    file = models.FileField(
        upload_to="troubleshooting_imports/%Y/%m/",
    )

    original_file_name = models.CharField(max_length=255)

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="troubleshooting_imports",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="processing",
    )

    total_records = models.PositiveIntegerField(default=0)
    imported_records = models.PositiveIntegerField(default=0)
    skipped_records = models.PositiveIntegerField(default=0)
    failed_records = models.PositiveIntegerField(default=0)

    error_log = models.TextField(
        blank=True,
        default="",
    )

    uploaded_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Troubleshooting Import"
        verbose_name_plural = "Troubleshooting Imports"
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.original_file_name} - {self.status}"

class SolutionAttachment(models.Model):
    solution_attachment_id = models.CharField(
        primary_key=True,
        max_length=36,
        default=uuid4, 
        editable=False
    )
    solution = models.ForeignKey(Solution, on_delete=models.CASCADE, related_name='attachments')
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    file = models.FileField(upload_to='solution_attachments/', null=True, blank=True)
    file_type = models.CharField(
        max_length=20,
        choices=[('file', 'File'), ('image', 'Image'), ('link', 'Link')],
        default='file'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

class Tag(models.Model):
    tag_name = models.CharField(max_length=50)
    class Meta:
        verbose_name = "Tag"              
        verbose_name_plural = "Tag"
class ProblemTag(models.Model):
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    class Meta:
        verbose_name = "ProblemTag"              
        verbose_name_plural = "ProblemTag"