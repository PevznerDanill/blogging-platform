from django.urls import path
from .views import (
    UserBlogListView,
    BlogCreateView,
    BlogDetailView,
    PostCreateView,
    PostDetailView,
    PostEditView,
    publish_or_archive,
    LatestPostsView,
)
from django.shortcuts import redirect, reverse


app_name = 'app_blog'

urlpatterns = [
    path('blog/<int:pk>/', UserBlogListView.as_view(), name='user_blog_list'),
    path('new-blog/', BlogCreateView.as_view(), name='blog_new'),
    path('blog-detail/<int:pk>/', BlogDetailView.as_view(), name='blog_detail'),
    path('new-post/<int:pk>/', PostCreateView.as_view(), name='post_new'),
    path('post-detail/<int:pk>/', PostDetailView.as_view(), name='post_detail'),
    path('post-edit/<int:pk>/', PostEditView.as_view(), name='post_edit'),
    path('publish-archive/<int:pk>/', publish_or_archive, name='publish_or_archive'),
    path('posts-latest/', LatestPostsView.as_view(), name='posts_latest'),
    path('', lambda req: redirect(reverse('app_blog:posts_latest')))
]