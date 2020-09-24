"""atelier URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from atelier import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.HomePageView.as_view(), name='index'),
    path('my-profile', views.MyProfileView.as_view(), name='my_profile'),
    path('users/', views.UserListView.as_view(), name='user_management'),
    path('users/create', views.UserCreateView.as_view(), name='user_management_create'),
    path('users/edit/<int:user_id>', views.UserUpdateView.as_view(), name='user_management_edit'),
    path('users/<int:user_id>', views.UserDetailView.as_view(), name='user_management_detail'),
    # authentication
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('auth/confirm-code/<int:user_id>/<str:type>', views.ConfirmCodeView.as_view(), name='confirm_code'),
    path('auth/code-not-received/<int:user_id>/<str:type>', views.CodeNotReceivedView.as_view(),
         name='code_not_received'),
    path('auth/logout/', views.LogoutView.as_view(), name='logout'),
    # path('auth/signup/', views.SignupView.as_view(), name='register'),
    path('auth/confirm-email/<int:user_id>/<str:token>/', views.ConfirmEmailView.as_view(), name='confirm_email'),
    path('auth/reset-password/', views.PasswordResetView.as_view(), name='reset_password'),
    path('auth/reset-password-confirm/<str:token>/',
         views.ConfirmPasswordResetView.as_view(), name='reset_password_confirm'),

]
