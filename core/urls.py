from rest_framework.authtoken.views import obtain_auth_token
from django.urls import path, include
from . import views 
from .views import CustomAuthToken
from .views import RegisterView
from rest_framework import routers
from .views import ProblemViewSet

router = routers.DefaultRouter()
router.register(r'problems', ProblemViewSet)

urlpatterns = [
    path('problems/', views.problem_list, name='problem_list'),
    path('api/', include(router.urls)),
    path('register/', RegisterView.as_view(), name='register'),
    path('register/', views.register_view, name='register'),
    path('api/register/', views.register_user, name='register_user'),
    path('problem/new/', views.problem_create, name='problem_create'),
    path('api-token-auth/', CustomAuthToken.as_view(), name='custom_api_token_auth'),
    path('api-token-auth/', obtain_auth_token, name='api_token_auth'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('problem/<int:pk>/', views.problem_detail, name='problem_detail'),
    path('problem/new/', views.problem_create, name='problem_create'),
]