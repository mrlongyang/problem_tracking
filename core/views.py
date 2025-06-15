from django.shortcuts import render, get_object_or_404, redirect
from .models import Problem
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
from .forms import RegisterForm, ProblemForm
from .models import Problem, ProblemAttachment
from .forms import ProblemForm, ProblemAttachmentForm
from rest_framework.decorators import api_view
from .models import User
from .serializers import UserSerializer  # You must define this
from django.contrib.auth.hashers import make_password

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
    return redirect('login')


# @login_required
# def problem_create(request):
#     if request.method == 'POST':
#         form = ProblemForm(request.POST)
#         if form.is_valid():
#             problem = form.save(commit=False)
#             problem.created_by = request.user
#             problem.department = request.user.department
#             problem.save()
#             return redirect('problem_list')
#     else:
#         form = ProblemForm()
#     return render(request, 'core/problem_form.html', {'form': form})


@login_required
def problem_list(request):
    problems = Problem.objects.all()
    return render(request, 'core/problem_list.html', {'problems': problems})

@login_required
def problem_detail(request, pk):
    problem = get_object_or_404(Problem, pk=pk)
    return render(request, 'core/problem_detail.html', {'problem': problem})

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

    return render(request, 'core/problem_form.html', {
        'form': form,
        'attachment_form': attachment_form
    })