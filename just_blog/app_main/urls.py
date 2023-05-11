from django.urls import path
from .views import IndexView, AboutView, ContactView


app_name = 'app_main'

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('about/', AboutView.as_view(), name='about'),
    path('contacts/', ContactView.as_view(), name='contacts')
]
