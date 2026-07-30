from pathlib import Path
from django import forms
from django.contrib.auth import get_user_model
from django.forms.widgets import FileInput

from .models import (
    Problem,
    Solution,
    ProblemAttachment,
    SolutionAttachment,
    Department,
)


User = get_user_model()


class ProblemForm(forms.ModelForm):
    class Meta:
        model = Problem
        fields = [
            "problem_id",
            "transaction_code",
            "error_code",
            "function_name",
            "title",
            "description",
            "priority",
            "status",
            "department",
            "module",
        ]

        widgets = {
            "problem_id": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Example: AI8808",
                }
            ),
            "transaction_code": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Example: 0015191",
                }
            ),
            "error_code": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Example: AI8808",
                }
            ),
            "function_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Example: GL A/C Information Query",
                }
            ),
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Error message",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": "Root cause or error details",
                }
            ),
            "priority": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "status": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "department": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "module": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Prevent changing the primary key during edit.
        if self.instance and self.instance.pk:
            self.fields["problem_id"].disabled = True


class RegisterForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Password",
            }
        ),
        label="Password",
    )

    confirm_password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Confirm password",
            }
        ),
        label="Confirm Password",
    )

    class Meta:
        model = User
        fields = [
            "user_id",
            "name",
            "email",
            "password",
        ]

        widgets = {
            "user_id": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                }
            ),
        }

    def clean(self):
        cleaned_data = super().clean()

        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error(
                "confirm_password",
                "Passwords do not match.",
            )

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])

        if commit:
            user.save()

        return user


class UserForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Leave blank to keep current password",
            }
        ),
        required=False,
    )

    class Meta:
        model = User
        fields = [
            "email",
            "name",
            "user_group",
            "role",
            "is_active",
            "is_staff",
            "password",
        ]

        widgets = {
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                }
            ),
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),
            "user_group": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "role": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "is_active": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
            "is_staff": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
        }

    def save(self, commit=True):
        user = super().save(commit=False)

        password = self.cleaned_data.get("password")

        if password:
            user.set_password(password)

        if commit:
            user.save()

        return user


class SolutionForm(forms.ModelForm):
    class Meta:
        model = Solution
        fields = [
            "content",
            "solution_type",
            "is_final_solution",
        ]

        widgets = {
            "content": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 6,
                    "placeholder": "Write the solution here...",
                }
            ),
            "solution_type": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "is_final_solution": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
        }


class MultiFileInput(FileInput):
    allow_multiple_selected = True


class AttachmentUploadForm(forms.Form):
    attachments = forms.FileField(
        widget=MultiFileInput(
            attrs={
                "multiple": True,
                "class": "form-control",
            }
        ),
        required=False,
    )


class ProblemAttachmentForm(forms.Form):
    attachments = forms.FileField(
        widget=MultiFileInput(
            attrs={
                "multiple": True,
                "class": "form-control",
            }
        ),
        required=False,
    )


class ImportGuideForm(forms.Form):
    file = forms.FileField(
        label="Troubleshooting Word Document",
        help_text="Only Microsoft Word .docx files are supported.",
        widget=forms.ClearableFileInput(
            attrs={
                "class": "form-control",
                "accept": ".docx",
            }
        ),
    )

    default_priority = forms.ChoiceField(
        choices=Problem.PRIORITY,
        initial="Medium",
        widget=forms.Select(
            attrs={
                "class": "form-select",
            }
        ),
    )

    default_department = forms.ModelChoiceField(
        queryset=Department.objects.all().order_by("department_name"),
        required=False,
        empty_label="Select department",
        widget=forms.Select(
            attrs={
                "class": "form-select",
            }
        ),
    )

    overwrite_existing = forms.BooleanField(
        required=False,
        initial=False,
        label="Update existing records with the same error code",
        widget=forms.CheckboxInput(
            attrs={
                "class": "form-check-input",
            }
        ),
    )

    def clean_file(self):
        uploaded_file = self.cleaned_data["file"]

        extension = Path(uploaded_file.name).suffix.lower()

        if extension != ".docx":
            raise forms.ValidationError(
                "Please upload a Microsoft Word .docx file."
            )

        max_size = 10 * 1024 * 1024

        if uploaded_file.size > max_size:
            raise forms.ValidationError(
                "The file must not be larger than 10 MB."
            )

        return uploaded_file