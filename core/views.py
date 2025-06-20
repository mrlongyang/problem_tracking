from django.shortcuts import render, get_object_or_404, redirect
from .models import Problem, ProblemAttachment, Menu, Permission
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from .serializers import ProblemSerializer, RegisterSerializer
from .forms import RegisterForm, ProblemForm, ProblemAttachmentForm, SolutionAttachmentForm
from rest_framework.decorators import api_view
from .models import User
from .serializers import UserSerializer
from django.contrib.auth.hashers import make_password
from django.http import HttpResponseForbidden
from .forms import UserForm
from .models import Problem, Solution, SolutionAttachment
from .forms import SolutionForm  # make sure your form is imported
import uuid


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


#User Manager
@login_required
def profile_view(request):
    return render(request, 'core/User_Profile/profile.html', {'user_obj': request.user})

from django.contrib.auth.decorators import login_required
@login_required
def dashboard_view(request):
    if not Permission.objects.filter(menu_id__menu_id='dashboard', role=request.user.role).exists():
        return HttpResponseForbidden("You are not allowed to access This Page 🚫")
    menus = Menu.objects.filter(permission__role=request.user.role)
    return render(request, 'core/dashboard.html', {'menus': menus})

@login_required
def user_manager_view(request):
    if not request.user.role:
        return HttpResponseForbidden()
    users = User.objects.all()
    return render(request, 'core/User_Management/user_manager.html', {'users': users})

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
    user = get_object_or_404(User, pk=pk)
    return render(request, 'core/User_Management/user_detail.html', {'user_obj': user})

@login_required
def user_edit_view(request, pk):
    user = get_object_or_404(User, pk=pk)
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
    user = get_object_or_404(User, pk=pk)
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

class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            return Response({'token': token.key}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Registration successful.")
            return redirect('login')  # or 'home'
    else:
        form = RegisterForm()
    return render(request, 'core/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('problem_list')  # or any dashboard
        else:
            messages.error(request, 'Invalid email or password')
    return render(request, 'core/login.html')

def logout_view(request):
    logout(request)
    return redirect('')


@login_required
def problem_list(request):
    problems = Problem.objects.all()
    return render(request, 'core/Problems/problem_list.html', {'problems': problems})


@login_required
def problem_detail(request, pk):
    problem = get_object_or_404(Problem, pk=pk)
    solutions = problem.solutions.all()
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

            return redirect('problem_detail', pk=pk)
    else:
        form = SolutionForm()

    return render(request, 'core/Problems/problem_detail.html', {
        'problem': problem,
        'solutions': solutions,
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
            return redirect('problem_list')
    else:
        form = ProblemForm()
        attachment_form = ProblemAttachmentForm()

    return render(request, 'core/Problems/problem_form.html', {
        'form': form,
        'attachment_form': attachment_form
    })

@login_required
def logout_confirm_view(request):
    if request.method == 'POST':
        logout(request)
        return redirect('login')  
    return redirect('dashboard')


def solution_create_view(request, problem_id):
    problem = Problem.objects.get(pk=problem_id)

    if request.method == 'POST':
        form = SolutionAttachmentForm(request.POST, request.FILES)
        if form.is_valid():
            # Create the solution
            solution = Solution.objects.create(
                problem=problem,
                author=request.user,
                content=request.POST.get('content', ''),
                is_final_solution=False,
                solution_type='text'
            )

            # Handle multiple attachments
            for file in request.FILES.getlist('attachments'):
                SolutionAttachment.objects.create(
                    solution=solution,
                    file=file,
                    uploaded_by=request.user,
                    file_type='file',
                    solution_attachment_id=str(uuid.uuid4())
                )

            return redirect('problem_detail', pk=problem_id)

    else:
        form = SolutionAttachmentForm()
    return render(request, 'core/Sulotions/solution_create.html', {'form': form, 'problem': problem})