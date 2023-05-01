from django.urls import path
from .feeds import LatestPostsFeed


app_name = 'app_rss'

urlpatterns = [
    path('', LatestPostsFeed(), name='posts_feed')
]