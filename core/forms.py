from django import forms
from django.contrib.auth import get_user_model
from .models import Problem, ProblemAttachment, SolutionAttachment
from core.models import User
from .models import Solution
from django.forms.widgets import FileInput
from django.forms import FileInput  # ✅ Add this import

class ProblemForm(forms.ModelForm):
    class Meta:
        model = Problem
        fields = ['title', 'description', 'priority', 'department', 'module']

class ProblemAttachmentForm(forms.Form):
    
    pass

User = get_user_model()

class RegisterForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['email', 'name', 'role', 'department']

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password1")
        p2 = cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords do not match")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
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
