from django import forms
from django.contrib.auth import get_user_model
from .models import Problem, ProblemAttachment, SolutionAttachment
from core.models import User
from .models import Solution
from django.forms.widgets import FileInput
from django.forms import FileInput  # ✅ Add this import
from django.core.exceptions import ValidationError

class ProblemForm(forms.ModelForm):
    class Meta:
        model = Problem
        fields = ['problem_id', 'title', 'description', 'priority', 'department', 'module']

class ProblemAttachmentForm(forms.Form):
    
    pass

User = get_user_model()

from django import forms
from .models import User

class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Password")
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")

    class Meta:
        model = User
        fields = ['user_id', 'name', 'email', 'password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error("confirm_password", "Passwords do not match")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])  # 🔐 hash password
        if commit:
            user.save()
        return user


class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, required=False)
    class Meta:
        model = User
        fields = ['email', 'name', 'user_group', 'role', 'is_active', 'is_staff', 'password']

# forms.py
class SolutionForm(forms.ModelForm):
    class Meta:
        model = Solution
        fields = ['content', 'is_final_solution']
        widgets = {
            'content': forms.Textarea(attrs={'placeholder': 'Write your solution here...'}),
        }
                  
class MultiFileInput(FileInput):
    allow_multiple_selected = True

class AttachmentUploadForm(forms.Form):
    attachments = forms.FileField(
        widget=MultiFileInput(attrs={'multiple': True}),
        required=False
    )
