from django.shortcuts import render, get_object_or_404, redirect
from .models import Problem, ProblemAttachment, Permission, Solution, SolutionAttachment, User, Module
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from .serializers import ProblemSerializer
from .forms import RegisterForm, ProblemForm, UserForm, SolutionForm, ProblemAttachmentForm, AttachmentUploadForm
from rest_framework.decorators import api_view
from .serializers import UserSerializer
from django.contrib.auth.hashers import make_password
from django.http import HttpResponseForbidden
import uuid
from django.utils import timezone
from django.db.models import Count
from django.utils.safestring import mark_safe
from datetime import timedelta
import json
from core.forms import RegisterForm
from django import forms
from django.core.paginator import Paginator
from django.db.models import Q
from django.urls import reverse
from django.http import JsonResponse
from django.template.loader import render_to_string


class ProblemViewSet(viewsets.ModelViewSet):
    queryset = Problem.objects.all().order_by('-created_at')
    serializer_class = ProblemSerializer
    permission_classes = [IsAuthenticated]

User = get_user_model()
class CustomAuthToken(APIView):
    def post(self, request, *args, **kwargs):
        email = request.data.get("email")
        password = request.data.get("password")
        if not email or not password:
            return Response({'error': 'Email and password are required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'Invalid email'}, status=status.HTTP_400_BAD_REQUEST)
        if not user.check_password(password):
            return Response({'error': 'Invalid password'}, status=status.HTTP_400_BAD_REQUEST)
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key})

# Function User Manager
@login_required
def profile_view(request):
    return render(request, 'core/User_Profile/profile.html', {'user_obj': request.user})

@login_required
def user_manager_view(request):
    if not request.user.role:
        return HttpResponseForbidden()
    users = User.objects.all()
    return render(request, 'core/Dashboard/User_Management/user_manager.html', {'users': users})

@login_required
def user_create_view(request):
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            pwd = form.cleaned_data.get('password')
            if pwd:
                user.set_password(pwd)
            user.save()
            return redirect('user_manager')
    else:
        form = UserForm()
    return render(request, 'core/User_Management/user_form.html', {'form': form, 'title': 'Create User'})

@login_required
def user_detail_view(request, pk):
    user = get_object_or_404(User, problem_id=pk)
    return render(request, 'core/User_Management/user_detail.html', {'user_obj': user})

@login_required
def user_edit_view(request, pk):
    user = get_object_or_404(User, problem_id=pk)
    if request.method == 'POST':
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            user = form.save(commit=False)
            pwd = form.cleaned_data.get('password')
            if pwd:
                user.set_password(pwd)
            user.save()
            return redirect('user_manager')
    else:
        form = UserForm(instance=user)
    return render(request, 'core/User_Management/user_form.html', {'form': form, 'title': 'Edit User'})

@login_required
def user_delete_view(request, pk):
    user = get_object_or_404(User, problem_id=pk)
    if request.method == 'POST':
        user.delete()
        return redirect('user_manager')
    return render(request, 'core/User_Management/user_confirm_delete.html', {'user_obj': user})


@login_required
def unauthorized_view(request):
    return render(request, 'core/User_Management/unauthorized.html', status=403)


@api_view(['POST'])
def register_user(request):
    data = request.data
    try:
        data['password'] = make_password(data['password'])  # hash the password
        serializer = UserSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'User created successfully'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

User = get_user_model()

class RegisterForm(forms.ModelForm):
    confirm_password = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = User
        fields = ['user_id', 'name', 'email', 'password']
        widgets = {
            'password': forms.PasswordInput()
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm = cleaned_data.get("confirm_password")

        if password and confirm and password != confirm:
            self.add_error("confirm_password", "Passwords do not match")

    
def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'core/Signup/register.html', {'form': form})


#Authentication
def login_view(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        password = request.POST.get('password')
        user = authenticate(request, user_id=user_id, password=password)
        
        if user is not None:
            login(request, user)
            if user.role and user.role.name.lower() == 'admin':
                return redirect('dashboard')
            else:
                return redirect('problem_list')
        else:
            messages.error(request, 'ID ຫຼື ລະຫັດຜ່ານບໍ່ຖືກຕ້ອງ!.')

    return render(request, 'core/Signup/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def logout_confirm_view(request):
    if request.method == 'POST':
        logout(request)
        return redirect('login')
    return redirect('dashboard')


#Function Manage Problem
@login_required
def problem_list(request):
    status = request.GET.get('status')
    search_query = request.GET.get('search', '')
    selected_priority = request.GET.get('priority', '')
    problems = Problem.objects.all()
    
    if status == 'open':
        problems = problems.filter(status='Open')
    elif status == 'resolved':
        problems = problems.filter(status='Resolved ✅')
        
    # ✅ Search by problem_id OR title (case-insensitive)
    if search_query:
        problems = problems.filter(
            Q(problem_id__icontains=search_query) | Q(title__icontains=search_query)
        )
    if selected_priority:
        problems = problems.filter(priority=selected_priority)

    paginator = Paginator(problems, 10) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'core/Problems/problem_list.html', {
        'problems': problems,
        'selected_status': status,
        'page_obj': page_obj,
        'search_query': search_query,
        'selected_priority': selected_priority,
    })
    
    
@login_required
def dashboard_problem_list(request):
    status = request.GET.get('status')
    search_query = request.GET.get('search', '')
    selected_priority = request.GET.get('priority', '')
    problems = Problem.objects.all()
    
    if status == 'open':
        problems = problems.filter(status='Open')
    elif status == 'resolved':
        problems = problems.filter(status='Resolved ✅')
        
    # ✅ Search by problem_id OR title (case-insensitive)
    if search_query:
        problems = problems.filter(
            Q(problem_id__icontains=search_query) | Q(title__icontains=search_query)
        )
    if selected_priority:
        problems = problems.filter(priority=selected_priority)

    paginator = Paginator(problems, 10) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'core/Dashboard/User_Management/dashboard_problem_list.html', {
        'problems': problems,
        'selected_status': status,
        'page_obj': page_obj,
        'search_query': search_query,
        'selected_priority': selected_priority,
    })


@login_required
def problem_detail(request, problem_id):
    problem = get_object_or_404(Problem, problem_id=problem_id)
    solutions = Solution.objects.filter(problem=problem).prefetch_related('attachments')
    solution_count = problem.solutions.count()
    solution = None  # predefine for safe rendering

    if request.method == 'POST':
        form = SolutionForm(request.POST, request.FILES)
        if form.is_valid():
            solution = form.save(commit=False)
            solution.problem = problem
            solution.author = request.user
            solution.save()

            # Handle file attachments
            for f in request.FILES.getlist('attachments'):
                SolutionAttachment.objects.create(
                    solution=solution,
                    file=f,
                    uploaded_by=request.user,
                    file_type='file'
                )
            if solution.is_final_solution:
                problem.status = "Resolved ✅"
                problem.save()
            messages.success(request, "ສົ່ງຄຳຕອບສຳເລັດ ✅")
            
            return redirect('problem_list')
    else:
        form = SolutionForm()
    return render(request, 'core/Problems/problem_detail.html', {
        'problem': problem,
        'solutions': solutions,
        'solution_count': solution_count,
        'form': form,
        'solution': solution  # None if not submitted
    })


@login_required
def problem_create(request):
    if request.method == 'POST':
        form = ProblemForm(request.POST)
        attachment_form = ProblemAttachmentForm(request.POST, request.FILES)

        if form.is_valid():
            problem = form.save(commit=False)
            problem.created_by = request.user
            problem.save()

            # ✅ This handles all uploaded files
            for file in request.FILES.getlist('files'):
                ProblemAttachment.objects.create(
                    problem=problem,
                    file=file,
                    uploaded_by=request.user
                )
            messages.success(request, "✅ ສຳເລັດ")
            return redirect('problem_list')
    else:
        form = ProblemForm()
        attachment_form = ProblemAttachmentForm()
    return render(request, 'core/Problems/problem_create.html', {
        'form': form,
        'attachment_form': attachment_form
    })


# Function Create Solution
@login_required
def solution_create_view(request, problem_id):
    problem = get_object_or_404(Problem, problem_id=problem_id)

    if request.method == 'POST':
        form = SolutionForm(request.POST)
        attachment_form = AttachmentUploadForm(request.POST, request.FILES)

        if form.is_valid() and attachment_form.is_valid():
            solution = form.save(commit=False)
            solution.problem = problem
            solution.author = request.user
            solution.solution_type = 'text'
            solution.save()
            # Handle attachments
            for file in request.FILES.getlist('attachments'):
                SolutionAttachment.objects.create(
                    solution=solution,
                    file=file,
                    uploaded_by=request.user,
                    file_type='file',
                    solution_attachment_id=str(uuid.uuid4())
                )
            # Update status
            if solution.is_final_solution:
                problem.status = "Resolved ✅"
                problem.last_updated = timezone.now()
                problem.save()
            return redirect('problem_detail', problem_id=problem_id)
    else:
        form = SolutionForm()
        attachment_form = AttachmentUploadForm()
    return render(request, 'core/Solutions/solution_create.html', {
        'form': form,
        'attachment_form': attachment_form,
        'problem': problem
    })


# Function Get Notification
def problem_notification(request):
    unresolved_count = 0
    latest_problem_link = ''
    
    if request.user.is_authenticated:
        unresolved = Problem.objects.exclude(status__in=['Closed', 'Resolved ✅']).order_by('-created_at')
        unresolved_count = unresolved.count()
        if unresolved.exists():
            latest_problem_link = reverse('problem_detail', kwargs={'pk': unresolved.first().pk})

    return {
        'notification_count': unresolved_count,
        'latest_problem_link': latest_problem_link
    }

# Function count Module problem
def most_problematic_module(request):
    to_module = Module.objects.annotate(problem_count=Count('problem')).order_by('-problem_count').first()
    
    return render(request, 'core/Problems/most_problematic_module.html', {
        'to_module': to_module
    })
    
# New Dashboard
@login_required
def dashboard_view(request):
    # Permission check
    if not Permission.objects.filter(menu_id__menu_id='dashboard', role=request.user.role).exists():
        return HttpResponseForbidden("You have no permission to access this Page! 🚫")
    problems = Problem.objects.all()
    resolved_issues = problems.filter(status="Resolved ✅").count()
    unresolved_issues = problems.exclude(status="Resolved ✅").count()
    # Calculate average resolution time from created_at to updated_at
    resolved_problems = problems.filter(
        status="Resolved ✅",
        created_at__isnull=False,
        updated_at__isnull=False
    )

    if resolved_problems.exists():
        total_days = sum(
            [(p.updated_at - p.created_at).days for p in resolved_problems],
            0
        )
        avg_days = total_days / resolved_problems.count()
    else:
        avg_days = 0

    # Status and Priority Chart Data
    status_counts = problems.values('status').annotate(count=Count('status'))
    priority_counts = problems.values('priority').annotate(count=Count('priority'))

    context = {
        'total_issues': problems.count(),
        'resolved_issues': resolved_issues,
        'unresolved_issues': unresolved_issues,
        'avg_resolution_days': round(avg_days, 1),
        'status_labels': mark_safe(json.dumps([s['status'] for s in status_counts])),
        'status_data': mark_safe(json.dumps([s['count'] for s in status_counts])),
        'priority_labels': mark_safe(json.dumps([p['priority'] for p in priority_counts])),
        'priority_data': mark_safe(json.dumps([p['count'] for p in priority_counts])),
    }
    return render(request, 'core/Dashboard/User_Management/dashboard.html', context)


@login_required
def settings_view(request):
    # Example settings logic: handle user profile update
    if request.method == 'POST':
        form = UserForm(request.POST, instance=request.user)
        if form.is_valid():
            user = form.save(commit=False)
            pwd = form.cleaned_data.get('password')
            if pwd:
                user.set_password(pwd)
            user.save()
            messages.success(request, "Settings updated successfully.")
            return redirect('settings')
    else:
        form = UserForm(instance=request.user)
    return render(request, 'core/Settings/settings.html', {'form': form})


@login_required
def report_issue_view(request):
    if request.method == 'POST':
        form = ProblemForm(request.POST, request.FILES)
        if form.is_valid():
            problem = form.save(commit=False)
            problem.created_by = request.user
            problem.save()
            # Handle attachments if any
            for file in request.FILES.getlist('files'):
                ProblemAttachment.objects.create(
                    problem=problem,
                    file=file,
                    uploaded_by=request.user
                )
            messages.success(request, "Issue reported successfully.")
            return redirect('problem_list')
    else:
        form = ProblemForm()
    return render(request, 'core/Problems/report_issue.html', {'form': form})


@login_required
def system_logs_view(request):
    # Example: Read logs from a file (customize the path as needed)
    log_file_path = 'logs/system.log'
    logs = []
    try:
        with open(log_file_path, 'r', encoding='utf-8') as f:
            logs = f.readlines()
    except FileNotFoundError:
        logs = ["Log file not found."]
    return render(request, 'core/Problems/system_logs.html', {'logs': logs})

def ajax_search_problems(request):
    query = request.GET.get('search', '')
    problems = Problem.objects.all()

    if query:
        problems = problems.filter(
            Q(problem_id__icontains=query) |
            Q(title__icontains=query)
        )

    html = render_to_string('core/Problems/_problem_table_body.html', {'problems': problems})
    return JsonResponse({'html': html})