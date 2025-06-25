from rest_framework.authtoken.views import obtain_auth_token
from django.urls import path, include
from . import views
from .views import CustomAuthToken
from .views import RegisterView
from rest_framework import routers
from .views import ProblemViewSet
from .views import dashboard_view, unauthorized_view, solution_create_view, user_manager_view, user_create_view
from django.contrib.auth import views as auth_views


router = routers.DefaultRouter()
router.register(r'problems', ProblemViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    
    #Dashboard Url Rout
    path('dashboard/', dashboard_view, name='dashboard'),
    path('dashboard/users/', views.user_manager_view, name='user_manager'),
    path('settings/', views.settings_view, name='settings'),
    path('dashboard/report-issue/', views.report_issue_view, name='report_issue'),
    path('dashboard/system-logs/', views.system_logs_view, name='system_logs'),
    

    

    #User Url Rout
    path('unauthorized/', unauthorized_view, name='unauthorized'),
    # path('users/', views.user_manager_view, name='user_manager'),
    path('users/create/', views.user_create_view, name='user_create'),
    path('users/<str:pk>/', views.user_detail_view, name='user_detail'),
    path('users/<str:pk>/edit/', views.user_edit_view, name='user_edit'),
    path('users/<str:pk>/delete/', views.user_delete_view, name='user_delete'),

    #Problem Url Rout
    path('problems/', views.problem_list, name='problem_list'),
    path('problem/<int:pk>/', views.problem_detail, name='problem_detail'),
    path('problem/new/', views.problem_create, name='problem_create'),
    # urls.py
    path('problem/<int:problem_id>/add-solution/', solution_create_view, name='solution_create'),


    #User Profile Manage Url Rout
    # path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('profile/', views.profile_view, name='profile_view'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('logout/confirm/', views.logout_confirm_view, name='logout_confirm'),
    

    #Register Url Rout
    # path('api-token-auth/', obtain_auth_token, name='api_token_auth'),
    path('register/', views.register_view, name='register'),
    path('api/register/', views.register_user, name='register_user'),
    path('api-token-auth/', CustomAuthToken.as_view(), name='custom_api_token_auth'),
    
]