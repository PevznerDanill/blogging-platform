from django.urls import path
from django.shortcuts import reverse, redirect
from .models import Profile
from .views import (
    GetStartedView,
    update_view,
    ProfileDetailView,
    MyLoginView,
    MyLogoutView,
    ProfilePublicView,
)


app_name = 'app_auth'

urlpatterns = [
    path('get-started/', GetStartedView.as_view(), name='get_started'),
    path('profile-update/<int:pk>/', update_view, name='profile_update'),
    path('profile-details/<int:pk>/', ProfileDetailView.as_view(), name='profile_detail'),
    path('login/', MyLoginView.as_view(), name='login'),
    path('logout/', MyLogoutView.as_view(), name='logout'),
    path('', lambda req: redirect(reverse('app_auth:profile_detail', kwargs={'pk': Profile.objects.get(user=req.user).pk}))),
    path('profile/<int:pk>/', ProfilePublicView.as_view(), name='profile_public')
]
