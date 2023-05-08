from django.urls import path
from .views import (
    ProfileListApiView,
    ProfileCreateApiView,
    BlogCreateApiView,
    BlogListApiView,
    BlogDetailApiView,
    PostCreateApiView,
    PostUpdateApiView,
    ImageCreateApiView,
    ImageDetailApiView,
    PostListApiView,
    ProfileUpdateApiView,
)

app_name = 'app_api'

urlpatterns = [
    path('profiles/', ProfileListApiView.as_view(), name='profile_list'),
    path('new-profile/', ProfileCreateApiView.as_view(), name='new_profile'),
    path('new-blog/', BlogCreateApiView.as_view(), name='new_blog'),
    path('blogs/', BlogListApiView.as_view(), name='blog_list'),
    path('blog/<int:pk>/', BlogDetailApiView.as_view(), name='blog_detail'),
    path('new-post/', PostCreateApiView.as_view(), name='new_post'),
    path('post/<int:pk>/', PostUpdateApiView.as_view(), name='post_detail'),
    path('new-image/', ImageCreateApiView.as_view(), name='new_image'),
    path('image/<int:pk>/', ImageDetailApiView.as_view(), name='image_detail'),
    path('posts/', PostListApiView.as_view(), name='post_list'),
    path('profile/<int:pk>/', ProfileUpdateApiView.as_view(), name='profile_update')
]

