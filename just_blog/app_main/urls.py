from django.urls import path
from .views import IndexView, AboutView, ContactView
from django.views.decorators.cache import cache_page


app_name = 'app_main'

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('about/', cache_page(60**2*24)(AboutView.as_view()), name='about'),
    path('contacts/', cache_page(60**2*24)(ContactView.as_view()), name='contacts')
]
