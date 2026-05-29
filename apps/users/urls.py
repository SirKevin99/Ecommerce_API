# apps/users/urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from apps.users import views

urlpatterns = [
    # Autenticación
    path("register/",        views.RegisterView.as_view(),       name="register"),
    path("login/",           views.LoginView.as_view(),          name="login"),
    path("logout/",          views.LogoutView.as_view(),         name="logout"),
    path("token/refresh/",   TokenRefreshView.as_view(),         name="token-refresh"),

    # Perfil
    path("profile/",         views.ProfileView.as_view(),        name="profile"),
    path("change-password/", views.ChangePasswordView.as_view(), name="change-password"),
]