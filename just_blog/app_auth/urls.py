from django.urls import path
from .views import GetStartedView, update_view


app_name = 'app_auth'

urlpatterns = [
    path('get-started/', GetStartedView.as_view(), name='get_started'),
    path('profile-update/<int:pk>/', update_view, name='profile_update')
]
