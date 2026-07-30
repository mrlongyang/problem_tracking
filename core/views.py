import mimetypes
import re
import uuid

from io import BytesIO

from docx.document import Document as DocumentClass
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph

from docx import Document
from django.db import transaction
from django.core.files.base import ContentFile
from django.shortcuts import render, get_object_or_404, redirect
from .models import Module, Problem, ProblemAttachment, Permission, Solution, SolutionAttachment, User
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
from django.utils.timezone import now
from django.db.models.functions import TruncDate
from django.db.models.functions import TruncMonth
from xhtml2pdf import pisa
from django.template.loader import get_template
from django.http import HttpResponse
from io import BytesIO 
from django.utils.dateparse import parse_date
from datetime import datetime
from .forms import ImportGuideForm
from django.db.models import Count, Q
from django.shortcuts import redirect, render



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
    return render(request, 'core/Dashboard/User_Management/user_form.html', {'form': form, 'title': 'Create User'})

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
            messages.error(request, 'ໄອດີ ຫຼື ລະຫັດຜ່ານບໍ່ຖືກຕ້ອງ!.')

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


# Function Problem List
@login_required
def problem_list(request):
    # Get filter values
    selected_status = request.GET.get("status", "").strip()
    search_query = request.GET.get("search", "").strip()
    selected_priority = request.GET.get("priority", "").strip()
    selected_module = request.GET.get("module", "").strip()
    start_date_str = request.GET.get("start_date", "").strip()
    end_date_str = request.GET.get("end_date", "").strip()

    # Start with all problems
    problems = (
        Problem.objects
        .select_related("module", "department")
        .all()
        .order_by("-created_at")
    )

    # Search filter
    if search_query:
        problems = problems.filter(
            Q(problem_id__icontains=search_query)
            | Q(title__icontains=search_query)
            | Q(description__icontains=search_query)
        )

    # Status filter
    if selected_status:
        problems = problems.filter(
            status__iexact=selected_status
        )

    # Priority filter
    if selected_priority:
        problems = problems.filter(
            priority__iexact=selected_priority
        )

    # Module filter
    if selected_module:
        problems = problems.filter(
            module__module_name__iexact=selected_module
        )

    # Start date filter
    if start_date_str:
        try:
            start_date = datetime.strptime(
                start_date_str,
                "%Y-%m-%d",
            ).date()

            problems = problems.filter(
                created_at__date__gte=start_date
            )
        except ValueError:
            messages.error(
                request,
                "Invalid start date format.",
            )
            return redirect("problem_list")

    # End date filter
    if end_date_str:
        try:
            end_date = datetime.strptime(
                end_date_str,
                "%Y-%m-%d",
            ).date()

            problems = problems.filter(
                created_at__date__lte=end_date
            )
        except ValueError:
            messages.error(
                request,
                "Invalid end date format.",
            )
            return redirect("problem_list")

    # AJAX live search
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        filtered = problems.values(
            "problem_id",
            "title",
            "description",
            "module__module_name",
            "status",
            "department__department_name",
            "updated_at",
        )

        return JsonResponse({
            "results": list(filtered),
        })

    # Module report
    module_report = []

    for module in Module.objects.all().order_by("module_name"):
        module_report.append({
            "module_name": module.module_name,
            "count": Problem.objects.filter(module=module).count()
        })

    # Counts before pagination
    total_issues = problems.count()

    open_count = Problem.objects.filter(
        status__iexact="open"
    ).count()

    resolved_count = Problem.objects.filter(
        status__iexact="resolved"
    ).count()

    # Pagination
    paginator = Paginator(problems, 10)
    page_obj = paginator.get_page(
        request.GET.get("page")
    )

    context = {
        "problems": problems,
        "page_obj": page_obj,
        "selected_status": selected_status,
        "selected_priority": selected_priority,
        "selected_module": selected_module,
        "search_query": search_query,
        "start_date": start_date_str,
        "end_date": end_date_str,
        "module_report": module_report,
        "total_issues": total_issues,
        "resolved_count": resolved_count,
        "open_count": open_count,
    }

    return render(
        request,
        "core/Problems/problem_list_standalone.html",
        context,
    )
    
# Edit problem record
@login_required
def problem_edit(request, problem_id):
    problem = get_object_or_404(Problem, problem_id=problem_id)
    
    if request.method == 'POST':
        form = ProblemForm(request.POST, instance=problem)
        if form.is_valid():
            form.save()
            messages.success(request, "ແກ້ໄຂບັນຫາສຳເລັດ ✅")
            return redirect('problem_list')
    else:
        form = ProblemForm(instance=problem)
        
    
    attachments = ProblemAttachment.objects.filter(problem=problem)
    
    return render(request, 'core/Problems/problem_edit.html', {
        'form': form,
        'problem': problem,
        'attachments': attachments,
    })
    
    
# Delete Problem Function
@login_required
def problem_delete(request, problem_id):
    problem = get_object_or_404(Problem, problem_id=problem_id)
    
    if request.method == 'POST':
        problem.delete()
        messages.success(request, "ລົບສຳເລັດ ✅")
        return redirect('problem_list')
    
    return render(request, 'core/Problems/problem_confirm_delete.html', {
        'problem': problem
    })


# Export PDF Function
def export_problems_pdf(request):
    status = request.GET.get('status')
    search_query = request.GET.get('search', '')
    selected_priority = request.GET.get('priority', '')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    selected_module = request.GET.get('module')

    problems = Problem.objects.all()

    # ✅ Filter by status
    if status == 'open':
        problems = problems.filter(status='Open')
    elif status == 'resolved':
        problems = problems.filter(status='Resolved ✅')

    # ✅ Filter by search
    if search_query:
        problems = problems.filter(
            Q(problem_id__icontains=search_query) |
            Q(title__icontains=search_query)
        )

    # ✅ Filter by priority
    if selected_priority:
        problems = problems.filter(priority=selected_priority)

    # ✅ Filter by module
    if selected_module and selected_module != 'None':
        problems = problems.filter(module__module_name__iexact=selected_module)

    
    # ✅ Filter by valid start and end dates
    parsed_start_date = None 
    parsed_end_date = None
    
    try:
        if start_date_str and end_date_str and start_date_str != 'None' and end_date_str != 'None':
            parsed_start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            parsed_end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            problems = problems.filter(created_at__date__range=(parsed_start_date, parsed_end_date))
    except ValueError:
        messages.error(request, "Invalid date format.")
        return redirect('problem_list')

    # ✅ Render PDF
    template = get_template('core/Problems/problem_pdf.html')
    
    
    context = {
        'problems': problems,
        'start_date': parsed_start_date,
        'end_date': parsed_end_date,
    }
    
    html = template.render(context)
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="filtered_problems_report.pdf"'

    pisa_status = pisa.CreatePDF(html, dest=response, encoding='utf-8')

    if pisa_status.err:
        return HttpResponse('PDF export error ❌')
    return response


# Function Dashboard Problem List
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

    paginator = Paginator(problems, 20) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'core/Dashboard/User_Management/dashboard_problem_list.html', {
        'problems': problems,
        'selected_status': status,
        'page_obj': page_obj,
        'search_query': search_query,
        'selected_priority': selected_priority,
    })


# Function Problem Detail
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
            messages.success(request, "ບັນທຶກວິທີແກ້ໄຂບັນຫາສຳເລັດ ✅")
            
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


# Function Create Problem
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
            messages.success(request, "✅ ສຳເລັດ", extra_tags="from_create")
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
    total_users = User.objects.count()
    # Calculate average resolution time from created_at to updated_at
    resolved_problems = problems.filter(
        status="Resolved ✅",
        created_at__isnull=False,
        updated_at__isnull=False
    )
    
    monthly_data = (
        Problem.objects
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(total=Count('problem_id'))
        .order_by('month')
    )
    
    months = [item['month'].strftime("%b %Y") for item in monthly_data]
    counts = [item['total'] for item in monthly_data]

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
        'total_users': total_users,
        'monthly_labels': months,
        'monthly_data': counts,
    }
    return render(request, 'core/Dashboard/User_Management/dashboard.html', context)


# Function Settings
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


def iterate_word_blocks(parent):
    """Yield paragraphs and tables in the order they appear in the Word file."""
    if isinstance(parent, DocumentClass):
        parent_element = parent.element.body
    else:
        parent_element = parent._tc

    for child in parent_element.iterchildren():
        if child.tag == qn("w:p"):
            yield Paragraph(child, parent)
        elif child.tag == qn("w:tbl"):
            yield Table(child, parent)


def extract_images_from_paragraph(paragraph):
    """Extract inline/floating images attached to a Word paragraph."""
    extracted_images = []
    seen_relationship_ids = set()

    for blip in paragraph._element.xpath(".//a:blip"):
        relationship_id = blip.get(qn("r:embed"))

        if not relationship_id or relationship_id in seen_relationship_ids:
            continue

        seen_relationship_ids.add(relationship_id)
        image_part = paragraph.part.related_parts.get(relationship_id)

        if image_part is None:
            continue

        content_type = getattr(image_part, "content_type", "image/png")
        extension = mimetypes.guess_extension(content_type) or ".png"

        extracted_images.append(
            {
                "data": image_part.blob,
                "filename": f"{uuid.uuid4()}{extension}",
                "content_type": content_type,
            }
        )

    return extracted_images


def build_module_id(module_name):
    """Create a short module primary key from a Word module heading."""
    module_id = re.sub(r"[^A-Za-z0-9]+", "_", module_name.strip()).strip("_")
    return (module_id or "IMPORTED")[:20].upper()


@login_required
def import_guide(request):
    if request.method == "POST":
        form = ImportGuideForm(request.POST, request.FILES)

        if form.is_valid():
            uploaded_file = form.cleaned_data["file"]
            default_priority = form.cleaned_data["default_priority"]
            default_department = form.cleaned_data["default_department"]
            overwrite_existing = form.cleaned_data["overwrite_existing"]

            try:
                document = Document(uploaded_file)

                # Examples:
                # 1 BP1231 : [ERROR MESSAGE]
                # 2 DD1007: [ANOTHER ERROR]
                error_pattern = re.compile(
                    r"^\s*\d+\s+([A-Za-z]{1,10}\d+)\s*[:：]\s*\[(.+?)\]\.?\s*$"
                )

                records = []
                current_module_name = ""
                current_record = None
                current_section = None

                for block in iterate_word_blocks(document):
                    if not isinstance(block, Paragraph):
                        continue

                    text = block.text.strip()

                    # A screenshot can be in a paragraph with no text.
                    paragraph_images = extract_images_from_paragraph(block)

                    if text.lower().startswith("function module"):
                        if current_record:
                            records.append(current_record)
                            current_record = None
                            current_section = None

                        module_match = re.search(r"[（(]\s*(.*?)\s*[）)]", text)
                        if module_match:
                            current_module_name = module_match.group(1).strip()
                        continue

                    error_match = error_pattern.match(text)

                    if error_match:
                        if current_record:
                            records.append(current_record)

                        error_code = error_match.group(1).strip()
                        title = error_match.group(2).strip()

                        current_record = {
                            "problem_id": error_code,
                            "error_code": error_code,
                            "title": title,
                            "module_name": current_module_name,
                            "root_cause_lines": [],
                            "resolution_lines": [],
                            "images": [],
                        }
                        current_section = None

                        if paragraph_images:
                            current_record["images"].extend(paragraph_images)
                        continue

                    if current_record is None:
                        continue

                    if paragraph_images:
                        current_record["images"].extend(paragraph_images)

                    normalized_text = text.lower().rstrip(":：").strip()

                    if normalized_text == "root cause":
                        current_section = "root_cause"
                        continue

                    if normalized_text == "resolution":
                        current_section = "resolution"
                        continue

                    if not text:
                        continue

                    if current_section == "root_cause":
                        current_record["root_cause_lines"].append(text)
                    elif current_section == "resolution":
                        current_record["resolution_lines"].append(text)

                if current_record:
                    records.append(current_record)

                if not records:
                    messages.warning(
                        request,
                        "No problem records were found in this Word document.",
                    )
                    return render(
                        request,
                        "core/Problems/import_guide.html",
                        {"form": form},
                    )

                imported_count = 0
                updated_count = 0
                skipped_count = 0
                attachment_count = 0

                with transaction.atomic():
                    for record in records:
                        module = None

                        if record["module_name"]:
                            module = Module.objects.filter(
                                module_name__iexact=record["module_name"]
                            ).first()

                            if module is None:
                                module, _ = Module.objects.get_or_create(
                                    module_id=build_module_id(record["module_name"]),
                                    defaults={
                                        "module_name": record["module_name"],
                                    },
                                )

                        root_cause = "\n".join(
                            record["root_cause_lines"]
                        ).strip()

                        resolution = "\n".join(
                            record["resolution_lines"]
                        ).strip()

                        existing_problem = Problem.objects.filter(
                            problem_id=record["problem_id"]
                        ).first()

                        problem_defaults = {
                            "error_code": record["error_code"],
                            "title": record["title"],
                            "description": root_cause or "Root cause not provided.",
                            "priority": default_priority,
                            "status": "Open",
                            "department": default_department,
                            "module": module,
                            "created_by": request.user,
                            "source_type": "word_import",
                            "source_file_name": uploaded_file.name,
                        }

                        if existing_problem:
                            if not overwrite_existing:
                                skipped_count += 1
                                continue

                            for field_name, value in problem_defaults.items():
                                setattr(existing_problem, field_name, value)

                            existing_problem.save()
                            problem = existing_problem
                            updated_count += 1

                            # Remove previous attachments before replacing them.
                            old_attachments = ProblemAttachment.objects.filter(
                                problem=problem
                            )
                            for old_attachment in old_attachments:
                                if old_attachment.file:
                                    old_attachment.file.delete(save=False)
                                old_attachment.delete()
                        else:
                            problem = Problem.objects.create(
                                problem_id=record["problem_id"],
                                **problem_defaults,
                            )
                            imported_count += 1

                        for image in record["images"]:
                            attachment = ProblemAttachment(
                                problem=problem,
                                uploaded_by=request.user,
                                file_type=image["content_type"],
                            )
                            attachment.file.save(
                                image["filename"],
                                ContentFile(image["data"]),
                                save=True,
                            )
                            attachment_count += 1

                        if resolution:
                            imported_solution = Solution.objects.filter(
                                problem=problem,
                                solution_type="imported",
                            ).first()

                            if imported_solution:
                                imported_solution.author = request.user
                                imported_solution.content = resolution
                                imported_solution.is_final_solution = True

                                # Only set this when the model contains the field.
                                if hasattr(imported_solution, "source_file_name"):
                                    imported_solution.source_file_name = uploaded_file.name

                                imported_solution.save()
                            else:
                                solution_data = {
                                    "problem": problem,
                                    "author": request.user,
                                    "content": resolution,
                                    "is_final_solution": True,
                                    "solution_type": "imported",
                                }

                                if any(
                                    field.name == "source_file_name"
                                    for field in Solution._meta.get_fields()
                                ):
                                    solution_data["source_file_name"] = uploaded_file.name

                                Solution.objects.create(**solution_data)

                messages.success(
                    request,
                    (
                        "Import completed. "
                        f"Created: {imported_count}, "
                        f"Updated: {updated_count}, "
                        f"Skipped: {skipped_count}, "
                        f"Images: {attachment_count}."
                    ),
                )
                return redirect("problem_list")

            except Exception as error:
                messages.error(request, f"Import failed: {error}")

    else:
        form = ImportGuideForm()

    return render(
        request,
        "core/Problems/import_guide.html",
        {"form": form},
    )